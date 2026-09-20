---
tags: [codegraph, module, layer/contracts]
layer: Contracts
source: backend/app/models/incident.py
fan_in: 5
fan_out: 0
symbols: 4
community: -1
---

# `app.models.incident`

> Structured representation of a parsed safety incident.

Layer: [[Contracts]] · `backend/app/models/incident.py` · 52 lines · 4 symbols

## Depends on

_Nothing in this package._

## Depended on by

- [[app.db.crud]] — instantiates ×1
- [[app.models]] — imports ×1
- [[app.models.output]] — imports ×1
- [[app.models.risk]] — imports ×1
- [[app.tools.parsing]] — instantiates ×4

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `SeverityTier` | 10 |
| class | `EntityType` | 18 |
| class | `HazardEntity` | 26 |
| class | `IncidentReport` | 33 |

## External packages

`enum`, `pydantic`
