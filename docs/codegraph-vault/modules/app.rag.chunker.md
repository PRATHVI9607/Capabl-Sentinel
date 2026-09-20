---
tags: [codegraph, module, layer/retrieval]
layer: Retrieval
source: backend/app/rag/chunker.py
fan_in: 1
fan_out: 1
symbols: 5
community: 8
---

# `app.rag.chunker`

> Semantic chunking: split where the topic changes, not every N characters.

Layer: [[Retrieval]] · `backend/app/rag/chunker.py` · 77 lines · 5 symbols

## Depends on

- [[app.rag.embedder]] — calls, imports ×2

## Depended on by

- [[app.rag.compressor]] — calls, imports ×2

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `Chunk` | 26 |
| function | `split_sentences` | 32 |
| function | `split_sections` | 36 |
| function | `semantic_chunks` | 47 |
| function | `_chunk_body` | 56 |

## External packages

`dataclasses`, `numpy`, `re`
