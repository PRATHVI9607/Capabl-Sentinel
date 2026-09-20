---
tags: [codegraph, module, layer/retrieval]
layer: Retrieval
source: backend/app/ingest/preprocessor.py
fan_in: 1
fan_out: 0
symbols: 3
community: 6
---

# `app.ingest.preprocessor`

> Turn raw page text into clean prose: drop running headers, fix line wrapping.

Layer: [[Retrieval]] · `backend/app/ingest/preprocessor.py` · 45 lines · 3 symbols

## Depends on

_Nothing in this package._

## Depended on by

- [[app.pipeline]] — calls, imports ×2

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `clean_pages` | 20 |
| function | `normalize` | 29 |
| function | `_repeated_lines` | 37 |

## External packages

`collections`, `re`
