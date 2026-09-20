"""One analysis, end to end: PDF in, persisted AnalysisReport out.

The API layer owns HTTP; this module owns the run. Everything it does is
wrapped so a background task can never raise into uvicorn, and every run is
bounded by a timeout so one pathological document cannot occupy a worker.
"""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

from .agents.graph import run_graph
from .agents.state import initial_state
from .cache import client as cache
from .config import settings
from .db import crud
from .db.session import session_factory
from .ingest.loader import DocumentLoadError, load_pdf
from .ingest.preprocessor import clean_pages
from .models import AnalysisReport, StreamUpdate
from .stream import broker

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "analysis:"

# Bounds how many analyses embed at once. See settings.max_concurrent_analyses.
_slots = asyncio.Semaphore(settings.max_concurrent_analyses)

# What a caller is told when something unexpected breaks. The detail goes to
# the logs; an anonymous uploader gets no stack trace, path or driver message.
GENERIC_FAILURE = "Analysis failed. The document could not be processed."


def cache_key(file_hash: str) -> str:
    return f"{CACHE_KEY_PREFIX}{file_hash}"


async def run_analysis(analysis_id: str, pdf_path: Path, file_name: str, file_hash: str) -> None:
    """Execute the graph and persist the result. Never raises."""
    started_at = time.monotonic()
    if _slots.locked():
        await broker.publish(
            analysis_id,
            StreamUpdate(
                stage="queued",
                status="started",
                message="Another analysis is running. Yours starts next.",
            ),
        )
    try:
        # wait_for rather than asyncio.timeout: the latter is 3.11+ and the
        # deployment target runs 3.10.
        async with _slots:
            report = await asyncio.wait_for(
                _analyse(analysis_id, pdf_path, file_name, started_at),
                timeout=settings.analysis_timeout_seconds,
            )
    except DocumentLoadError as exc:
        # Safe to surface: it describes the caller's own file, nothing internal.
        await _fail(analysis_id, str(exc))
        return
    except asyncio.TimeoutError:
        logger.warning("Analysis %s exceeded %ss", analysis_id, settings.analysis_timeout_seconds)
        await _fail(analysis_id, "Analysis timed out. Try a shorter document.")
        return
    except Exception:
        logger.exception("Analysis %s crashed", analysis_id)
        await _fail(analysis_id, GENERIC_FAILURE)
        return
    finally:
        pdf_path.unlink(missing_ok=True)

    async with session_factory() as session:
        await crud.save_report(session, report)
    await cache.set(cache_key(file_hash), analysis_id, settings.analysis_cache_ttl_seconds)

    await broker.publish(
        analysis_id,
        StreamUpdate(
            stage="complete",
            status="completed",
            message="Analysis complete",
            data=report.model_dump(mode="json"),
        ),
    )
    broker.close(analysis_id)


async def _analyse(analysis_id: str, pdf_path: Path, file_name: str, started_at: float) -> AnalysisReport:
    # pdfplumber is synchronous and CPU-bound; off the event loop it goes.
    pages = await asyncio.to_thread(load_pdf, pdf_path)
    text = clean_pages(pages)

    state = initial_state(analysis_id, file_name, text, started_at)
    final_state = await run_graph(state)

    report = final_state.get("analysis_report")
    if report is None:
        raise RuntimeError(final_state.get("error") or "Pipeline produced no report")
    return AnalysisReport.model_validate(report)


async def _fail(analysis_id: str, message: str) -> None:
    async with session_factory() as session:
        await crud.mark_failed(session, analysis_id, message)
    await broker.publish(analysis_id, StreamUpdate(stage="error", status="error", message=message))
    broker.close(analysis_id)
