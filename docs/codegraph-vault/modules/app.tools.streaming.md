---
tags: [codegraph, module, layer/tools]
layer: Tools
source: backend/app/tools/streaming.py
fan_in: 3
fan_out: 3
symbols: 1
community: 10
---

# `app.tools.streaming`

> Publish a pipeline update to whichever SSE clients are watching this analysis.

Layer: [[Tools]] · `backend/app/tools/streaming.py` · 14 lines · 1 symbols

## Depends on

- [[app.models]] — imports ×1
- [[app.models.output]] — instantiates ×1
- [[app.stream]] — calls, imports ×2

## Depended on by

- [[app.agents.nodes.base]] — calls ×3
- [[app.agents.nodes.error_handler]] — calls ×1
- [[app.tools]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `emit_stream_update` | 9 |
