---
tags: [codegraph, module, layer/contracts]
layer: Contracts
source: backend/app/models/retrieval.py
fan_in: 4
fan_out: 0
symbols: 3
community: -1
---

# `app.models.retrieval`

> Models for everything that comes back out of the retrieval layer.

Layer: [[Contracts]] · `backend/app/models/retrieval.py` · 38 lines · 3 symbols

## Depends on

_Nothing in this package._

## Depended on by

- [[app.models]] — imports ×1
- [[app.models.output]] — imports ×1
- [[app.rag.retriever]] — instantiates ×1
- [[app.tools.retrieval]] — instantiates ×2

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `RetrievedChunk` | 8 |
| class | `SimilarIncident` | 19 |
| class | `RegulatoryClause` | 31 |

## External packages

`pydantic`
