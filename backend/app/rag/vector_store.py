"""Vector search façade over two real backends.

Default is `local_store`: an exact numpy search over an index file, which is
faster than a network call at this corpus size and needs no credential.
Setting QDRANT_URL switches every call to `qdrant_store` instead, for corpora
large enough that an approximate index beats an exhaustive scan.

Both backends are used in anger -- this is not an interface with one
implementation.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence

import numpy as np

from ..config import settings
from . import local_store, qdrant_store

logger = logging.getLogger(__name__)

LOCAL = "local"
QDRANT = "qdrant"


def backend() -> str:
    return QDRANT if settings.qdrant_url else LOCAL


def configured() -> bool:
    """True when the selected backend can actually answer a query."""
    if backend() == QDRANT:
        return qdrant_store.reachable()
    return bool(local_store.load(settings.incidents_collection).chunk_ids)


def ensure_collection(name: str) -> None:
    if backend() == QDRANT:
        qdrant_store.ensure_collection(name)


def write_index(name: str, chunk_ids: Sequence[str], vectors: np.ndarray, payloads: Sequence[dict]) -> None:
    """Replace a collection's contents. Called by the ingest scripts only."""
    if backend() == QDRANT:
        qdrant_store.upsert(name, chunk_ids, vectors, payloads)
    else:
        local_store.save(name, chunk_ids, vectors, payloads)


def search(
    name: str, vector: np.ndarray, *, limit: int, metadata: dict[str, str] | None = None
) -> list[dict]:
    """Dense search returning payload dicts carrying `_id` and `_score`.

    Never raises: retrieval degrades to "no evidence found" rather than
    failing the whole analysis.
    """
    if backend() == QDRANT:
        return qdrant_store.search(name, vector, limit=limit, metadata=metadata)
    return local_store.load(name).search(vector, limit=limit, metadata=metadata)


def fetch_payloads(name: str, chunk_ids: Iterable[str]) -> dict[str, dict]:
    """Payloads for chunks BM25 matched but the dense search missed."""
    ids = list(chunk_ids)
    if not ids:
        return {}
    if backend() == QDRANT:
        return qdrant_store.fetch_payloads(name, ids)
    return local_store.load(name).payloads_for(ids)
