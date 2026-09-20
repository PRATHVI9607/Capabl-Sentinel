---
tags: [codegraph, module, layer/providers]
layer: Providers
source: backend/app/stream.py
fan_in: 3
fan_out: 3
symbols: 9
community: 6
---

# `app.stream`

> In-process pub/sub between the analysis background task and SSE subscribers.

Layer: [[Providers]] · `backend/app/stream.py` · 110 lines · 9 symbols

## Depends on

- [[app.config]] — imports ×1
- [[app.models]] — imports ×1
- [[app.models.output]] — instantiates ×3

## Depended on by

- [[app.api.analyze]] — calls, imports ×3
- [[app.pipeline]] — calls, imports ×3
- [[app.tools.streaming]] — calls, imports ×2

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `_Channel` | 25 |
| class | `StreamBroker` | 32 |
| method | `__init__` | 40 |
| method | `open` | 43 |
| method | `publish` | 47 |
| method | `close` | 55 |
| method | `subscribe` | 62 |
| method | `_evict_expired` | 95 |
| function | `_is_terminal` | 105 |

## External packages

`asyncio`, `collections`, `dataclasses`, `time`
