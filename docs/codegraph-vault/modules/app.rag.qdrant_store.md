---
tags: [codegraph, module, layer/retrieval]
layer: Retrieval
source: backend/app/rag/qdrant_store.py
fan_in: 1
fan_out: 2
symbols: 9
community: 8
---

# `app.rag.qdrant_store`

> Qdrant backend, used when QDRANT_URL is set.

Layer: [[Retrieval]] · `backend/app/rag/qdrant_store.py` · 147 lines · 9 symbols

## Depends on

- [[app.config]] — imports ×1
- [[app.rag.embedder]] — imports ×1

## Depended on by

- [[app.rag.vector_store]] — calls, imports ×6

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `point_id` | 27 |
| function | `_client` | 32 |
| function | `reachable` | 47 |
| function | `_require_client` | 60 |
| function | `ensure_collection` | 67 |
| function | `upsert` | 82 |
| function | `_build_filter` | 101 |
| function | `search` | 112 |
| function | `fetch_payloads` | 133 |

## External packages

`collections`, `functools`, `logging`, `numpy`, `typing`, `uuid`
