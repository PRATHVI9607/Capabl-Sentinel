---
tags: [codegraph, module, layer/orchestration]
layer: Orchestration
source: backend/app/agents/graph.py
fan_in: 1
fan_out: 10
symbols: 4
community: 10
---

# `app.agents.graph`

> The SENTINEL state machine.

Layer: [[Orchestration]] · `backend/app/agents/graph.py` · 88 lines · 4 symbols

## Depends on

- [[app.agents.nodes.alert_synthesizer]] — imports, references ×2
- [[app.agents.nodes.document_router]] — imports ×1
- [[app.agents.nodes.entity_extractor]] — imports ×1
- [[app.agents.nodes.error_handler]] — imports, references ×2
- [[app.agents.nodes.incident_parser]] — imports ×1
- [[app.agents.nodes.pattern_detector]] — imports ×1
- [[app.agents.nodes.priority_alert_synthesizer]] — imports, references ×2
- [[app.agents.nodes.regulatory_auditor]] — imports ×1
- [[app.agents.nodes.risk_scorer]] — imports ×1
- [[app.agents.state]] — imports, references ×2

## Depended on by

- [[app.pipeline]] — calls, imports ×2

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `route_after_scoring` | 44 |
| function | `build_graph` | 52 |
| function | `sentinel_graph` | 80 |
| function | `run_graph` | 85 |

## External packages

`functools`, `langgraph`
