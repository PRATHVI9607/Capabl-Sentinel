---
tags: [codegraph, module, layer/orchestration]
layer: Orchestration
source: backend/app/agents/nodes/base.py
fan_in: 8
fan_out: 3
symbols: 5
community: 10
---

# `app.agents.nodes.base`

> Shared node plumbing: streaming, error capture, and the iteration guard.

Layer: [[Orchestration]] · `backend/app/agents/nodes/base.py` · 78 lines · 5 symbols

## Depends on

- [[app.agents.state]] — imports, references ×2
- [[app.tools]] — imports ×1
- [[app.tools.streaming]] — calls ×3

## Depended on by

- [[app.agents.nodes.alert_synthesizer]] — calls, imports, instantiates ×3
- [[app.agents.nodes.document_router]] — calls, imports, instantiates ×3
- [[app.agents.nodes.entity_extractor]] — calls, imports, instantiates ×3
- [[app.agents.nodes.incident_parser]] — calls, imports, instantiates ×3
- [[app.agents.nodes.pattern_detector]] — calls, imports, instantiates ×3
- [[app.agents.nodes.priority_alert_synthesizer]] — calls, imports, instantiates ×3
- [[app.agents.nodes.regulatory_auditor]] — calls, imports, instantiates ×3
- [[app.agents.nodes.risk_scorer]] — calls, imports, instantiates ×3

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `NodeResult` | 21 |
| function | `node` | 32 |
| function | `decorator` | 44 |
| function | `run` | 46 |
| function | `_fail` | 72 |

## External packages

`collections`, `dataclasses`, `functools`, `logging`
