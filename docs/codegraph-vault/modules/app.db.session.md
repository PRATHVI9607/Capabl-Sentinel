---
tags: [codegraph, module, layer/providers]
layer: Providers
source: backend/app/db/session.py
fan_in: 3
fan_out: 2
symbols: 2
community: 6
---

# `app.db.session`

> Async engine and session factory.

Layer: [[Providers]] · `backend/app/db/session.py` · 33 lines · 2 symbols

## Depends on

- [[app.config]] — imports ×1
- [[app.db.models]] — imports ×1

## Depended on by

- [[app.deps]] — imports, references ×2
- [[app.main]] — calls, imports ×2
- [[app.pipeline]] — calls, imports ×3

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `init_models` | 20 |
| function | `get_session` | 30 |

## External packages

`collections`, `sqlalchemy`
