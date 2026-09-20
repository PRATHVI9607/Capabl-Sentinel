---
tags: [codegraph, module, layer/retrieval]
layer: Retrieval
source: backend/app/rag/local_store.py
fan_in: 1
fan_out: 2
symbols: 8
community: 8
---

# `app.rag.local_store`

> Brute-force vector search over a numpy array held in memory.

Layer: [[Retrieval]] · `backend/app/rag/local_store.py` · 123 lines · 8 symbols

## Depends on

- [[app.config]] — imports ×1
- [[app.rag.embedder]] — imports ×1

## Depended on by

- [[app.rag.vector_store]] — calls, imports ×6

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `vectors_path` | 34 |
| function | `sidecar_path` | 38 |
| class | `LocalIndex` | 43 |
| method | `search` | 48 |
| method | `payloads_for` | 67 |
| method | `_matching` | 75 |
| function | `load` | 94 |
| function | `save` | 115 |

## External packages

`collections`, `dataclasses`, `functools`, `json`, `logging`, `numpy`, `pathlib`
