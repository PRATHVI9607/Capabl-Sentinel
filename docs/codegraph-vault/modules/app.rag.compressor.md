---
tags: [codegraph, module, layer/retrieval]
layer: Retrieval
source: backend/app/rag/compressor.py
fan_in: 1
fan_out: 2
symbols: 2
community: 8
---

# `app.rag.compressor`

> Contextual compression: drop the sentences of a chunk that miss the query.

Layer: [[Retrieval]] · `backend/app/rag/compressor.py` · 55 lines · 2 symbols

## Depends on

- [[app.rag.chunker]] — calls, imports ×2
- [[app.rag.embedder]] — calls, imports ×3

## Depended on by

- [[app.rag.retriever]] — calls, imports ×2

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `compress_all` | 21 |
| function | `_keep` | 48 |

## External packages

`numpy`
