---
tags: [codegraph, module, layer/orchestration]
layer: Orchestration
source: backend/app/agents/nodes/incident_parser.py
fan_in: 2
fan_out: 4
symbols: 1
community: 10
---

# `app.agents.nodes.incident_parser`

> Extract the structured incident from the report text.

Layer: [[Orchestration]] · `backend/app/agents/nodes/incident_parser.py` · 33 lines · 1 symbols

## Depends on

- [[app.agents.nodes.base]] — calls, imports, instantiates ×3
- [[app.agents.state]] — imports ×1
- [[app.tools]] — imports ×1
- [[app.tools.parsing]] — calls ×1

## Depended on by

- [[app.agents.graph]] — imports ×1
- [[app.agents.nodes]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `incident_parser` | 11 |
