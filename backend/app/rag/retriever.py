"""Hybrid retrieval: BM25 + dense, merged with RRF, reranked by a cross-encoder.

Three independent quality controls: sparse recall catches exact regulation
numbers, dense recall catches paraphrase, and the cross-encoder resolves the
ordering the two disagree on.
"""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache

from ..config import settings
from ..models import RetrievedChunk
from . import vector_store
from .bm25_index import BM25Index
from .compressor import compress_all
from .embedder import embed_query

logger = logging.getLogger(__name__)

RRF_K = 60
CANDIDATES_PER_SOURCE = 20


def reciprocal_rank_fusion(result_lists: list[list[str]], *, k: int = RRF_K) -> list[str]:
    """Merge ranked id lists: score(doc) = sum over lists of 1 / (rank + k).

    k=60 is the constant from the original RRF paper; raising it flattens the
    advantage held by the top of each individual list.
    """
    scores: dict[str, float] = {}
    for ranked_ids in result_lists:
        for rank, doc_id in enumerate(ranked_ids):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rank + k)
    return sorted(scores, key=lambda doc_id: scores[doc_id], reverse=True)


@lru_cache(maxsize=4)
def _bm25_for(collection: str) -> BM25Index | None:
    return BM25Index.load(settings.data_dir / f"bm25_{collection}.pkl")


@lru_cache(maxsize=1)
def _reranker():
    try:
        from flashrank import Ranker

        return Ranker(model_name=settings.reranker_model, cache_dir=str(settings.data_dir / "flashrank"))
    except Exception as exc:  # noqa: BLE001 - reranking is an optimisation, not a requirement
        logger.warning("FlashRank unavailable, falling back to RRF order: %s", exc)
        return None


def _rerank(query: str, candidates: list[dict], top_k: int) -> list[dict]:
    ranker = _reranker()
    if ranker is None or not candidates:
        return candidates[:top_k]
    from flashrank import RerankRequest

    passages = [{"id": index, "text": item["text"]} for index, item in enumerate(candidates)]
    ranked = ranker.rerank(RerankRequest(query=query, passages=passages))
    ordered = []
    for entry in ranked[:top_k]:
        candidate = dict(candidates[int(entry["id"])])
        candidate["score"] = float(entry["score"])
        ordered.append(candidate)
    return ordered


async def hybrid_search(
    collection: str,
    query: str,
    *,
    k: int = 8,
    metadata: dict[str, str] | None = None,
    compress_results: bool = True,
) -> list[RetrievedChunk]:
    """Run both retrievers concurrently, fuse, rerank, and compress."""
    bm25 = _bm25_for(collection)

    dense_task = asyncio.to_thread(
        vector_store.search,
        collection,
        embed_query(query),
        limit=CANDIDATES_PER_SOURCE,
        metadata=metadata,
    )
    sparse_task = asyncio.to_thread(bm25.search, query, CANDIDATES_PER_SOURCE) if bm25 else _none()

    dense_hits, sparse_hits = await asyncio.gather(dense_task, sparse_task)

    payloads = {hit.get("chunk_id", hit["_id"]): hit for hit in dense_hits}
    sparse_ids = [chunk_id for chunk_id, _ in (sparse_hits or [])]
    missing = [chunk_id for chunk_id in sparse_ids if chunk_id not in payloads]
    payloads.update(vector_store.fetch_payloads(collection, missing))

    fused_ids = reciprocal_rank_fusion(
        [[hit.get("chunk_id", hit["_id"]) for hit in dense_hits], sparse_ids]
    )
    candidates = [
        {
            "chunk_id": chunk_id,
            "text": payloads[chunk_id].get("text", ""),
            "score": float(payloads[chunk_id].get("_score", 0.0)),
            "payload": payloads[chunk_id],
        }
        for chunk_id in fused_ids
        if chunk_id in payloads and payloads[chunk_id].get("text")
    ][:CANDIDATES_PER_SOURCE]

    top = _rerank(query, candidates, k)
    # One embedding pass for the whole result set, not one per chunk.
    texts = (
        compress_all(query, [item["text"] for item in top])
        if compress_results
        else [item["text"] for item in top]
    )
    return [
        RetrievedChunk(
            chunk_id=item["chunk_id"],
            text=text,
            score=item["score"],
            source_document=item["payload"].get("source_document", "unknown"),
            section=item["payload"].get("section", ""),
            metadata={
                key: str(value)
                for key, value in item["payload"].items()
                if key not in {"text", "_id", "_score"} and value is not None
            },
        )
        for item, text in zip(top, texts, strict=False)
    ]


async def _none() -> list[tuple[str, float]]:
    return []
