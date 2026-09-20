---
tags: [codegraph, module, layer/transport]
layer: Transport
source: backend/app/api/history.py
fan_in: 1
fan_out: 4
symbols: 3
community: 6
---

# `app.api.history`

> Past analyses: the list behind the incident explorer and the dashboard stats.

Layer: [[Transport]] · `backend/app/api/history.py` · 45 lines · 3 symbols

## Depends on

- [[app.db.crud]] — calls, imports ×4
- [[app.deps]] — imports ×1
- [[app.models]] — imports ×1
- [[app.models.output]] — references ×2

## Depended on by

- [[app.main]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `list_history` | 17 |
| function | `history_stats` | 34 |
| function | `get_history_entry` | 40 |

## External packages

`fastapi`
