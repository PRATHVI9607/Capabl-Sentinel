---
tags: [codegraph, module, layer/retrieval]
layer: Retrieval
source: backend/app/rag/vector_store.py
fan_in: 2
fan_out: 3
symbols: 6
community: 8
---

# `app.rag.vector_store`

> Vector search façade over two real backends.

Layer: [[Retrieval]] · `backend/app/rag/vector_store.py` · 73 lines · 6 symbols

## Depends on

- [[app.config]] — imports ×1
- [[app.rag.local_store]] — calls, imports ×6
- [[app.rag.qdrant_store]] — calls, imports ×6

## Depended on by

- [[app.api.health]] — calls, imports ×3
- [[app.rag.retriever]] — calls, imports ×2

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `backend` | 28 |
| function | `configured` | 32 |
| function | `ensure_collection` | 39 |
| function | `write_index` | 44 |
| function | `search` | 52 |
| function | `fetch_payloads` | 65 |

## External packages

`collections`, `logging`, `numpy`
