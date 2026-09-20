"""Qdrant backend, used when QDRANT_URL is set.

`qdrant_client` is imported lazily so the default local-index path does not pay
for it at startup.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Iterable, Sequence
from functools import lru_cache
from typing import Any

import numpy as np

from ..config import settings
from .embedder import EMBEDDING_DIM

logger = logging.getLogger(__name__)

# Stable point ids, so re-ingesting the same corpus replaces points rather than duplicating them.
_ID_NAMESPACE = uuid.UUID("6f1c0e9a-4c77-4d0a-9b83-2d5a1e5a7f11")
REQUEST_TIMEOUT_SECONDS = 30


def point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(_ID_NAMESPACE, chunk_id))


@lru_cache(maxsize=1)
def _client() -> Any | None:
    if not settings.qdrant_url:
        return None
    try:
        from qdrant_client import QdrantClient
    except ImportError:
        logger.error("QDRANT_URL is set but qdrant-client is not installed.")
        return None
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


def reachable() -> bool:
    """True when the configured cluster answers. Used by /health, never on the hot path."""
    client = _client()
    if client is None:
        return False
    try:
        client.get_collections()
    except Exception as exc:  # noqa: BLE001 - any failure means "not usable"
        logger.warning("Qdrant unreachable: %s", exc)
        return False
    return True


def _require_client() -> Any:
    client = _client()
    if client is None:
        raise RuntimeError("QDRANT_URL is not configured, or qdrant-client is not installed")
    return client


def ensure_collection(name: str) -> None:
    from qdrant_client import models

    client = _require_client()
    if client.collection_exists(name):
        return
    client.create_collection(
        collection_name=name,
        vectors_config=models.VectorParams(size=EMBEDDING_DIM, distance=models.Distance.COSINE),
    )


UPSERT_BATCH_SIZE = 256


def upsert(name: str, chunk_ids: Sequence[str], vectors: np.ndarray, payloads: Sequence[dict]) -> None:
    """Write points in batches, so a large corpus does not become one huge request."""
    from qdrant_client import models

    client = _require_client()
    for start in range(0, len(chunk_ids), UPSERT_BATCH_SIZE):
        window = slice(start, start + UPSERT_BATCH_SIZE)
        client.upsert(
            collection_name=name,
            points=[
                models.PointStruct(id=point_id(chunk_id), vector=vector.tolist(), payload=payload)
                for chunk_id, vector, payload in zip(
                    chunk_ids[window], vectors[window], payloads[window], strict=False
                )
            ],
            wait=True,
        )


def _build_filter(metadata: dict[str, str] | None) -> Any | None:
    from qdrant_client import models

    conditions = [
        models.FieldCondition(key=key, match=models.MatchValue(value=value))
        for key, value in (metadata or {}).items()
        if value
    ]
    return models.Filter(must=conditions) if conditions else None


def search(
    name: str, vector: np.ndarray, *, limit: int, metadata: dict[str, str] | None = None
) -> list[dict]:
    """Dense search. Returns payload dicts carrying `_id` and `_score`, or [] on failure."""
    client = _client()
    if client is None:
        return []
    try:
        hits = client.search(
            collection_name=name,
            query_vector=vector.tolist(),
            query_filter=_build_filter(metadata),
            limit=limit,
            with_payload=True,
        )
    except Exception as exc:  # noqa: BLE001 - retrieval failure degrades, it does not abort
        logger.warning("Qdrant search on %s failed: %s", name, exc)
        return []
    return [{**(hit.payload or {}), "_id": str(hit.id), "_score": hit.score} for hit in hits]


def fetch_payloads(name: str, chunk_ids: Iterable[str]) -> dict[str, dict]:
    client = _client()
    ids = [point_id(chunk_id) for chunk_id in chunk_ids]
    if client is None or not ids:
        return {}
    try:
        records = client.retrieve(collection_name=name, ids=ids, with_payload=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Qdrant retrieve on %s failed: %s", name, exc)
        return {}
    return {
        str((record.payload or {}).get("chunk_id", record.id)): dict(record.payload or {})
        for record in records
    }
