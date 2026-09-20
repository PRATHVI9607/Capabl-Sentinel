---
tags: [codegraph, module, layer/transport]
layer: Transport
source: backend/app/main.py
fan_in: 0
fan_out: 8
symbols: 4
community: 6
---

# `app.main`

> FastAPI application: CORS, rate limiting, security headers, routes, startup.

Layer: [[Transport]] · `backend/app/main.py` · 110 lines · 4 symbols

## Depends on

- [[app]] — imports ×1
- [[app.api.analyze]] — imports ×1
- [[app.api.health]] — imports ×1
- [[app.api.history]] — imports ×1
- [[app.api.tools]] — imports ×1
- [[app.cache.client]] — calls, imports ×2
- [[app.config]] — imports ×1
- [[app.db.session]] — calls, imports ×2

## Depended on by

_Nothing — an entry point, or unused._

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `lifespan` | 41 |
| function | `client_ip` | 71 |
| function | `security_headers` | 81 |
| function | `rate_limit` | 89 |

## External packages

`contextlib`, `fastapi`, `logging`, `urllib`
