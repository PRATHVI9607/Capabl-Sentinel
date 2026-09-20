---
tags: [codegraph, module, layer/retrieval]
layer: Retrieval
source: backend/app/rag/embedder.py
fan_in: 5
fan_out: 1
symbols: 3
community: 8
---

# `app.rag.embedder`

> bge-small-en-v1.5 embeddings. One model instance for the process.

Layer: [[Retrieval]] · `backend/app/rag/embedder.py` · 48 lines · 3 symbols

## Depends on

- [[app.config]] — imports ×1

## Depended on by

- [[app.rag.chunker]] — calls, imports ×2
- [[app.rag.compressor]] — calls, imports ×3
- [[app.rag.local_store]] — imports ×1
- [[app.rag.qdrant_store]] — imports ×1
- [[app.rag.retriever]] — calls, imports ×2

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `_model` | 28 |
| function | `embed_documents` | 37 |
| function | `embed_query` | 45 |

## External packages

`collections`, `functools`, `numpy`
