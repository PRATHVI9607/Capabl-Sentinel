---
tags: [codegraph, module, layer/retrieval]
layer: Retrieval
source: backend/app/ingest/classifier.py
fan_in: 1
fan_out: 1
symbols: 3
community: 9
---

# `app.ingest.classifier`

> Decide what kind of document was uploaded.

Layer: [[Retrieval]] · `backend/app/ingest/classifier.py` · 80 lines · 3 symbols

## Depends on

- [[app.llm]] — calls, imports ×2

## Depended on by

- [[app.agents.nodes.document_router]] — calls, imports ×2

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `_Verdict` | 46 |
| function | `score_keywords` | 50 |
| function | `classify` | 58 |

## External packages

`logging`, `pydantic`, `typing`
