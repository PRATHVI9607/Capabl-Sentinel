---
tags: [codegraph, module, layer/orchestration]
layer: Orchestration
source: backend/app/agents/state.py
fan_in: 13
fan_out: 0
symbols: 2
community: 10
---

# `app.agents.state`

> The typed state every LangGraph node reads from and writes to.

Layer: [[Orchestration]] · `backend/app/agents/state.py` · 67 lines · 2 symbols

## Depends on

_Nothing in this package._

## Depended on by

- [[app.agents.graph]] — imports, references ×2
- [[app.agents.nodes.alert_synthesizer]] — imports ×1
- [[app.agents.nodes.base]] — imports, references ×2
- [[app.agents.nodes.document_router]] — imports ×1
- [[app.agents.nodes.entity_extractor]] — imports ×1
- [[app.agents.nodes.error_handler]] — imports ×1
- [[app.agents.nodes.incident_parser]] — imports ×1
- [[app.agents.nodes.pattern_detector]] — imports ×1
- [[app.agents.nodes.priority_alert_synthesizer]] — imports ×1
- [[app.agents.nodes.regulatory_auditor]] — imports ×1
- [[app.agents.nodes.risk_scorer]] — imports ×1
- [[app.agents.nodes.synthesis]] — imports ×1
- [[app.pipeline]] — calls, imports ×2

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `SentinelState` | 10 |
| function | `initial_state` | 44 |

## External packages

`typing`
