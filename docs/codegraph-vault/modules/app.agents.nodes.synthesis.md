---
tags: [codegraph, module, layer/orchestration]
layer: Orchestration
source: backend/app/agents/nodes/synthesis.py
fan_in: 2
fan_out: 6
symbols: 4
community: 9
---

# `app.agents.nodes.synthesis`

> Shared assembly for both alert-synthesis paths.

Layer: [[Orchestration]] · `backend/app/agents/nodes/synthesis.py` · 129 lines · 4 symbols

## Depends on

- [[app.agents.state]] — imports ×1
- [[app.llm]] — calls, imports ×2
- [[app.models]] — imports ×1
- [[app.models.output]] — instantiates ×2
- [[app.tools]] — imports ×1
- [[app.tools.actions]] — calls ×1

## Depended on by

- [[app.agents.nodes.alert_synthesizer]] — calls, imports ×2
- [[app.agents.nodes.priority_alert_synthesizer]] — calls, imports ×2

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `synthesize` | 33 |
| function | `_title` | 74 |
| function | `_deterministic_description` | 80 |
| function | `_description` | 98 |

## External packages

`time`
