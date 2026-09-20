---
tags: [codegraph, module, layer/providers]
layer: Providers
source: backend/app/db/crud.py
fan_in: 3
fan_out: 4
symbols: 6
community: 6
---

# `app.db.crud`

> Every read and write against the analyses table.

Layer: [[Providers]] · `backend/app/db/crud.py` · 103 lines · 6 symbols

## Depends on

- [[app.db.models]] — imports, instantiates, references ×8
- [[app.models]] — imports ×1
- [[app.models.incident]] — instantiates ×1
- [[app.models.output]] — instantiates ×2

## Depended on by

- [[app.api.analyze]] — calls, imports ×3
- [[app.api.history]] — calls, imports ×4
- [[app.pipeline]] — calls, imports ×3

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `create_analysis` | 12 |
| function | `save_report` | 17 |
| function | `mark_failed` | 30 |
| function | `get_report` | 39 |
| function | `list_analyses` | 46 |
| function | `dashboard_stats` | 83 |

## External packages

`sqlalchemy`
