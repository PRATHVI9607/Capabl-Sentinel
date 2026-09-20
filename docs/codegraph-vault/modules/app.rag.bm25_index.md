---
tags: [codegraph, module, layer/retrieval]
layer: Retrieval
source: backend/app/rag/bm25_index.py
fan_in: 1
fan_out: 0
symbols: 6
community: 8
---

# `app.rag.bm25_index`

> Sparse keyword index. Built once by the ingest script, loaded read-only at runtime.

Layer: [[Retrieval]] · `backend/app/rag/bm25_index.py` · 60 lines · 6 symbols

## Depends on

_Nothing in this package._

## Depended on by

- [[app.rag.retriever]] — calls, imports ×2

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `tokenize` | 15 |
| class | `BM25Index` | 20 |
| method | `build` | 25 |
| method | `search` | 28 |
| method | `save` | 50 |
| method | `load` | 55 |

## External packages

`dataclasses`, `pathlib`, `pickle`, `rank_bm25`, `re`
