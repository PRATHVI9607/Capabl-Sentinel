---
tags: [codegraph, module, layer/transport]
layer: Transport
source: backend/app/api/health.py
fan_in: 1
fan_out: 4
symbols: 1
community: 8
---

# `app.api.health`

> Liveness endpoint. Also the UptimeRobot target that keeps Render warm.

Layer: [[Transport]] · `backend/app/api/health.py` · 28 lines · 1 symbols

## Depends on

- [[app]] — imports ×1
- [[app.config]] — imports ×1
- [[app.llm]] — calls, imports ×2
- [[app.rag.vector_store]] — calls, imports ×3

## Depended on by

- [[app.main]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `health` | 18 |

## External packages

`datetime`, `fastapi`
