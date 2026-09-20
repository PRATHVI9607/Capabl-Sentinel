"""Upload, stream, and fetch a single analysis."""

from __future__ import annotations

import hashlib
import re
import tempfile
import uuid
from pathlib import Path, PurePosixPath, PureWindowsPath

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from ..cache import client as cache
from ..config import settings
from ..db import crud
from ..deps import DbSession
from ..models import AnalysisReport
from ..pipeline import cache_key, run_analysis
from ..stream import broker

router = APIRouter(tags=["analyze"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    # Tell nginx and Render's proxy not to buffer the stream.
    "X-Accel-Buffering": "no",
}

UPLOAD_CHUNK_BYTES = 64 * 1024
PDF_MAGIC = b"%PDF"
MAX_FILENAME_LENGTH = 200
_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9 ._-]+")


def safe_filename(raw: str | None) -> str:
    """Strip any directory component and anything that is not plainly printable.

    The name is echoed back to the browser and used in log lines, so it is
    treated as untrusted input rather than as a path.
    """
    name = PureWindowsPath(PurePosixPath(raw or "").name).name
    name = _UNSAFE_FILENAME_CHARS.sub("_", name).strip(". ")
    return (name or "upload.pdf")[:MAX_FILENAME_LENGTH]


async def read_capped(file: UploadFile) -> bytes:
    """Read the upload, refusing it as soon as it passes the size limit.

    Reading in chunks means an oversized body is rejected partway rather than
    after it has been buffered in full.
    """
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(UPLOAD_CHUNK_BYTES):
        total += len(chunk)
        if total > settings.max_upload_bytes:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                f"File exceeds the {settings.max_upload_bytes // (1024 * 1024)}MB limit",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def validate(filename: str, content: bytes) -> None:
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only PDF files are supported")
    if len(content) < settings.min_upload_bytes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File appears to be empty or corrupt")
    if not content.startswith(PDF_MAGIC):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File is not a valid PDF")


@router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def start_analysis(
    background_tasks: BackgroundTasks,
    session: DbSession,
    file: UploadFile = File(...),
) -> dict[str, str]:
    """Accept a PDF and start the pipeline. Returns immediately with an analysis id."""
    file_name = safe_filename(file.filename)
    content = await read_capped(file)
    validate(file_name, content)

    file_hash = hashlib.sha256(content).hexdigest()
    if cached_id := await cache.get(cache_key(file_hash)):
        return {"analysis_id": cached_id, "status": "cached"}

    analysis_id = str(uuid.uuid4())
    await crud.create_analysis(session, analysis_id, file_name)

    # Written to disk because pdfplumber needs a real path. The name comes from
    # the generated id, never from the upload. The pipeline deletes it.
    handle, temp_path = tempfile.mkstemp(suffix=".pdf", prefix=f"sentinel-{analysis_id}-")
    with open(handle, "wb") as pdf:
        pdf.write(content)

    # Opened before the task starts, so a client that connects late replays from the start.
    broker.open(analysis_id)
    background_tasks.add_task(run_analysis, analysis_id, Path(temp_path), file_name, file_hash)
    return {"analysis_id": analysis_id, "status": "processing"}


@router.get("/analyze/{analysis_id}/stream")
async def stream_analysis(analysis_id: str) -> StreamingResponse:
    """Server-sent events: one per pipeline stage, ending with the full report."""

    async def events():
        async for update in broker.subscribe(analysis_id):
            yield f"data: {update.model_dump_json()}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers=SSE_HEADERS)


@router.get("/analyze/{analysis_id}", response_model=AnalysisReport)
async def get_analysis(analysis_id: str, session: DbSession) -> AnalysisReport:
    report = await crud.get_report(session, analysis_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found or still processing")
    return report
