"""Shared plumbing for the two one-off ingestion scripts."""

from __future__ import annotations

import hashlib
import re
import sys
from collections.abc import Iterator
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.ingest.loader import DocumentLoadError, load_pdf
from app.ingest.preprocessor import clean_pages, normalize
from app.rag import vector_store
from app.rag.bm25_index import BM25Index
from app.rag.chunker import semantic_chunks
from app.rag.embedder import embed_documents

EMBED_BATCH_SIZE = 64
METADATA_WINDOW = 8000

# Ingestion is a trusted local operation on documents an operator chose, so the
# upload-path budgets do not apply: truncating a reference document would weaken
# every later retrieval against it. CSB investigation reports run to hundreds of
# pages, well past the limits that bound an anonymous upload.
INGEST_MAX_PAGES = 2_000
INGEST_MAX_CHARS = 5_000_000

_DATE = re.compile(
    r"\b(?:on\s+)?((?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b"
)

INDUSTRY_TERMS: dict[str, tuple[str, ...]] = {
    "construction": (
        "construction site",
        "jobsite",
        "scaffold",
        "excavation",
        "roofing",
        "general contractor",
    ),
    "chemical": (
        "chemical",
        "refinery",
        "reactor",
        "process unit",
        "petrochemical",
        "distillation",
        "polymer",
        "catalyst",
        "feedstock",
    ),
    "manufacturing": (
        "plant floor",
        "assembly line",
        "machine shop",
        "production line",
        "stamping",
        "fabrication",
        "machining",
    ),
    "mining": ("mine", "quarry", "underground", "highwall", "wellhead", "drilling rig", "oilfield"),
    "agriculture": ("farm", "grain bin", "silo", "tractor", "harvest", "livestock"),
    "utilities": ("substation", "transmission line", "power plant", "switchyard", "transformer"),
    "warehousing": ("warehouse", "forklift", "distribution center", "pallet rack", "loading dock"),
    "healthcare": ("hospital", "clinic", "patient care", "nursing home"),
    "food": ("food processing", "meat processing", "poultry", "bakery", "brewery", "cold storage"),
}

# A single passing mention should not decide the label. Occurrences are counted
# rather than distinct terms present: a chemical plant report naming a
# "contractor" twice was being labelled construction, while the word "chemical"
# appeared hundreds of times. A clear margin over the runner-up is also
# required, so genuinely mixed documents stay "unknown" instead of guessing.
MIN_INDUSTRY_HITS = 5
INDUSTRY_MARGIN = 1.5

# Whole words only. Substring counting read 'mine' inside 'determined' and
# 'press' inside 'pressure', which labelled a grain mill as mining and made
# every pressurised-system report look like manufacturing.
_INDUSTRY_PATTERNS: dict[str, re.Pattern[str]] = {
    name: re.compile(r"\b(?:" + "|".join(re.escape(term) for term in terms) + r")\b", re.IGNORECASE)
    for name, terms in INDUSTRY_TERMS.items()
}


def read_document(path: Path) -> str:
    """Full text of a .pdf or .txt source document, without the upload budgets."""
    if path.suffix.lower() == ".txt":
        return normalize(path.read_text(encoding="utf-8", errors="replace"))
    return clean_pages(load_pdf(path, max_pages=INGEST_MAX_PAGES, max_chars=INGEST_MAX_CHARS))


def source_files(directory: Path) -> list[Path]:
    return sorted(p for p in directory.glob("*") if p.suffix.lower() in {".pdf", ".txt"})


def chunk_id_for(source: str, index: int, text: str) -> str:
    """Stable across re-ingests of unchanged text, so upserts replace rather than duplicate."""
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return f"{source}::{index}::{digest}"


def detect_industry(text: str) -> str:
    """Label a document by how often each industry's vocabulary appears.

    Returns "unknown" unless one industry clears MIN_INDUSTRY_HITS and leads the
    runner-up by INDUSTRY_MARGIN. Guessing from a single passing mention is worse
    than admitting the document is mixed: the label is shown in the UI and drives
    the retrieval filter.
    """
    scores = {name: len(pattern.findall(text)) for name, pattern in _INDUSTRY_PATTERNS.items()}
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    (best, top), (_, runner_up) = ranked[0], ranked[1]

    if top < MIN_INDUSTRY_HITS or top < runner_up * INDUSTRY_MARGIN:
        return "unknown"
    return best


def detect_date(text: str) -> str:
    match = _DATE.search(text)
    return match.group(1) if match else ""


def batched(items: list, size: int = EMBED_BATCH_SIZE) -> Iterator[list]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def index_chunks(collection: str, chunk_ids: list[str], payloads: list[dict]) -> None:
    """Embed every chunk, write the vector index, then the BM25 sidecar index."""
    if not chunk_ids:
        print("  nothing to index")
        return

    texts = [payload["text"] for payload in payloads]
    batches = []
    for batch in batched(texts):
        batches.append(embed_documents(batch))
        print(f"  embedded {sum(len(b) for b in batches)}/{len(texts)} chunks")
    vectors = np.vstack(batches)

    vector_store.ensure_collection(collection)
    vector_store.write_index(collection, chunk_ids, vectors, payloads)
    print(f"  vector index -> {vector_store.backend()} backend ({len(chunk_ids)} chunks)")

    # settings.data_dir, not a path relative to this file: the retriever reads
    # from the configured directory, and a hardcoded one silently writes the
    # index somewhere the reader never looks.
    path = settings.data_dir / f"bm25_{collection}.pkl"
    BM25Index.build(chunk_ids, texts).save(path)
    print(f"  BM25 index -> {path.name} ({len(chunk_ids)} chunks)")


__all__ = [
    "DocumentLoadError",
    "INGEST_MAX_CHARS",
    "INGEST_MAX_PAGES",
    "METADATA_WINDOW",
    "batched",
    "chunk_id_for",
    "detect_date",
    "detect_industry",
    "index_chunks",
    "read_document",
    "semantic_chunks",
    "source_files",
]
