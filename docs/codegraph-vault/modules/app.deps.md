---
tags: [codegraph, module, layer/transport]
layer: Transport
source: backend/app/deps.py
fan_in: 2
fan_out: 1
symbols: 0
community: 6
---

# `app.deps`

> FastAPI dependencies.

Layer: [[Transport]] · `backend/app/deps.py` · 13 lines · 0 symbols

## Depends on

- [[app.db.session]] — imports, references ×2

## Depended on by

- [[app.api.analyze]] — imports ×1
- [[app.api.history]] — imports ×1

## External packages

`fastapi`, `sqlalchemy`, `typing`
