---
tags: [codegraph, module, layer/providers]
layer: Providers
source: backend/app/cache/client.py
fan_in: 3
fan_out: 1
symbols: 7
community: 6
---

# `app.cache.client`

> Key/value cache over the Upstash REST API, with an in-process fallback.

Layer: [[Providers]] · `backend/app/cache/client.py` · 88 lines · 7 symbols

## Depends on

- [[app.config]] — imports ×1

## Depended on by

- [[app.api.analyze]] — imports ×1
- [[app.main]] — calls, imports ×2
- [[app.pipeline]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `_configured` | 21 |
| function | `_command` | 25 |
| function | `_local_get` | 34 |
| function | `get` | 45 |
| function | `set` | 56 |
| function | `incr_with_expiry` | 66 |
| function | `reset_local` | 85 |

## External packages

`httpx`, `logging`, `time`
