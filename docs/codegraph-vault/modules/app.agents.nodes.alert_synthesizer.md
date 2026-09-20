---
tags: [codegraph, module, layer/orchestration]
layer: Orchestration
source: backend/app/agents/nodes/alert_synthesizer.py
fan_in: 2
fan_out: 3
symbols: 1
community: 10
---

# `app.agents.nodes.alert_synthesizer`

> Standard synthesis path, taken when the risk score is below 8.0.

Layer: [[Orchestration]] · `backend/app/agents/nodes/alert_synthesizer.py` · 22 lines · 1 symbols

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
| function | `alert_synthesizer` | 11 |
