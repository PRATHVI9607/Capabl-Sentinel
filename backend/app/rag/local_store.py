"""Brute-force vector search over a numpy array held in memory.

For this corpus that is not a compromise, it is the right algorithm. 80
documents chunk to roughly 2,000 vectors; at 384 dimensions that is 3MB, and
an exhaustive cosine search is a single matmul -- well under a millisecond,
exact, with no network hop, no credential and no cold start.

Approximate nearest-neighbour indexing earns its keep somewhere north of
~100k vectors (150MB, ~40ms per query here). `app/rag/qdrant_store.py` is that
path; set QDRANT_URL to take it.

The on-disk format is a plain `.npz` of float32 vectors plus a JSON sidecar of
ids and payloads. Nothing is pickled, so loading an index file cannot execute
code.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from ..config import settings
from .embedder import EMBEDDING_DIM

logger = logging.getLogger(__name__)


def vectors_path(collection: str) -> Path:
    return settings.data_dir / f"vectors_{collection}.npz"


def sidecar_path(collection: str) -> Path:
    return settings.data_dir / f"vectors_{collection}.json"


@dataclass(frozen=True)
class LocalIndex:
    chunk_ids: tuple[str, ...]
    vectors: np.ndarray
    payloads: tuple[dict, ...]

    def search(
        self, vector: np.ndarray, *, limit: int, metadata: dict[str, str] | None = None
    ) -> list[dict]:
        candidates = self._matching(metadata)
        if candidates.size == 0:
            return []

        # Vectors are L2-normalised on write, so a dot product is the cosine similarity.
        scores = self.vectors[candidates] @ vector
        ranking = np.argsort(-scores)[:limit]
        return [
            {
                **self.payloads[candidates[position]],
                "_id": self.chunk_ids[candidates[position]],
                "_score": float(scores[position]),
            }
            for position in ranking
        ]

    def payloads_for(self, chunk_ids: Sequence[str]) -> dict[str, dict]:
        wanted = set(chunk_ids)
        return {
            chunk_id: payload
            for chunk_id, payload in zip(self.chunk_ids, self.payloads, strict=False)
            if chunk_id in wanted
        }

    def _matching(self, metadata: dict[str, str] | None) -> np.ndarray:
        """Positions passing the metadata filter; all of them when there is no filter."""
        wanted = {key: value for key, value in (metadata or {}).items() if value}
        if not wanted:
            return np.arange(len(self.chunk_ids))
        return np.array(
            [
                position
                for position, payload in enumerate(self.payloads)
                if all(payload.get(key) == value for key, value in wanted.items())
            ],
            dtype=int,
        )


EMPTY = LocalIndex(chunk_ids=(), vectors=np.empty((0, EMBEDDING_DIM), dtype=np.float32), payloads=())


@lru_cache(maxsize=4)
def load(collection: str) -> LocalIndex:
    """Read the index the ingest scripts built. Empty if it has not been built yet."""
    vectors_file, sidecar_file = vectors_path(collection), sidecar_path(collection)
    if not (vectors_file.exists() and sidecar_file.exists()):
        logger.warning("No local vector index for %s; retrieval will return nothing.", collection)
        return EMPTY

    sidecar = json.loads(sidecar_file.read_text(encoding="utf-8"))
    with np.load(vectors_file) as archive:
        vectors = archive["vectors"].astype(np.float32)

    chunk_ids = tuple(sidecar["chunk_ids"])
    payloads = tuple(sidecar["payloads"])
    if not len(chunk_ids) == len(payloads) == vectors.shape[0]:
        logger.error(
            "Local index for %s is inconsistent; ignoring it. Re-run the ingest script.", collection
        )
        return EMPTY
    return LocalIndex(chunk_ids=chunk_ids, vectors=vectors, payloads=payloads)


def save(collection: str, chunk_ids: Sequence[str], vectors: np.ndarray, payloads: Sequence[dict]) -> None:
    """Write the whole index. The ingest scripts build it once, in full."""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(vectors_path(collection), vectors=np.asarray(vectors, dtype=np.float32))
    sidecar_path(collection).write_text(
        json.dumps({"chunk_ids": list(chunk_ids), "payloads": list(payloads)}), encoding="utf-8"
    )
    load.cache_clear()
