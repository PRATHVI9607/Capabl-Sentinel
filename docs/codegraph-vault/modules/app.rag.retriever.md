---
tags: [codegraph, module, layer/retrieval]
layer: Retrieval
source: backend/app/rag/retriever.py
fan_in: 1
fan_out: 7
symbols: 6
community: 8
---

# `app.rag.retriever`

> Hybrid retrieval: BM25 + dense, merged with RRF, reranked by a cross-encoder.

Layer: [[Retrieval]] · `backend/app/rag/retriever.py` · 139 lines · 6 symbols

## Depends on

- [[app.config]] — imports ×1
- [[app.models]] — imports ×1
- [[app.models.retrieval]] — instantiates ×1
- [[app.rag.bm25_index]] — calls, imports ×2
- [[app.rag.compressor]] — calls, imports ×2
- [[app.rag.embedder]] — calls, imports ×2
- [[app.rag.vector_store]] — calls, imports ×2

## Depended on by

- [[app.tools.retrieval]] — calls, imports ×4

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `reciprocal_rank_fusion` | 27 |
| function | `_bm25_for` | 41 |
| function | `_reranker` | 46 |
| function | `_rerank` | 56 |
| function | `hybrid_search` | 72 |
| function | `_none` | 137 |

## External packages

`asyncio`, `functools`, `logging`
