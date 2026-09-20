---
tags: [codegraph, module, layer/orchestration]
layer: Orchestration
source: backend/app/agents/nodes/priority_alert_synthesizer.py
fan_in: 2
fan_out: 3
symbols: 1
community: 10
---

# `app.agents.nodes.priority_alert_synthesizer`

> Priority synthesis path, taken when the risk score reaches 8.0 or above.

Layer: [[Orchestration]] · `backend/app/agents/nodes/priority_alert_synthesizer.py` · 23 lines · 1 symbols

## Depends on

- [[app.agents.nodes.base]] — calls, imports, instantiates ×3
- [[app.agents.nodes.synthesis]] — calls, imports ×2
- [[app.agents.state]] — imports ×1

## Depended on by

- [[app.agents.graph]] — imports, references ×2
- [[app.agents.nodes]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `priority_alert_synthesizer` | 11 |
