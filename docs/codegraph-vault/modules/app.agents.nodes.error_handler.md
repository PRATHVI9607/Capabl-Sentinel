---
tags: [codegraph, module, layer/orchestration]
layer: Orchestration
source: backend/app/agents/nodes/error_handler.py
fan_in: 2
fan_out: 6
symbols: 2
community: 10
---

# `app.agents.nodes.error_handler`

> Terminal node for a failed run: emit what was produced before the failure.

Layer: [[Orchestration]] · `backend/app/agents/nodes/error_handler.py` · 82 lines · 2 symbols

## Depends on

- [[app.agents.state]] — imports ×1
- [[app.models]] — imports ×1
- [[app.models.output]] — instantiates ×2
- [[app.models.risk]] — instantiates ×2
- [[app.tools]] — imports ×1
- [[app.tools.streaming]] — calls ×1

## Depended on by

- [[app.agents.graph]] — imports, references ×2
- [[app.agents.nodes]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `_unscored` | 31 |
| function | `error_handler` | 50 |

## External packages

`logging`, `time`
