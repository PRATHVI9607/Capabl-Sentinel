---
tags: [codegraph, module, layer/providers]
layer: Providers
source: backend/app/db/models.py
fan_in: 2
fan_out: 0
symbols: 2
community: 6
---

# `app.db.models`

> SQLAlchemy tables. One row per analysis; the report itself is stored as JSON.

Layer: [[Providers]] · `backend/app/db/models.py` · 34 lines · 2 symbols

## Depends on

_Nothing in this package._

## Depended on by

- [[app.db.crud]] — imports, instantiates, references ×8
- [[app.db.session]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `Base` | 16 |
| class | `Analysis` | 20 |

## External packages

`datetime`, `sqlalchemy`
