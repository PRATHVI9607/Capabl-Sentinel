---
tags: [codegraph, module, layer/orchestration]
layer: Orchestration
source: backend/app/agents/nodes/regulatory_auditor.py
fan_in: 2
fan_out: 5
symbols: 1
community: 10
---

# `app.agents.nodes.regulatory_auditor`

> Retrieve the regulatory clauses that apply to this incident.

Layer: [[Orchestration]] · `backend/app/agents/nodes/regulatory_auditor.py` · 43 lines · 1 symbols

## Depends on

- [[app.agents.nodes.base]] — calls, imports, instantiates ×3
- [[app.agents.state]] — imports ×1
- [[app.models]] — imports ×1
- [[app.tools]] — imports ×1
- [[app.tools.retrieval]] — calls ×2

## Depended on by

- [[app.agents.graph]] — imports ×1
- [[app.agents.nodes]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `regulatory_auditor` | 14 |
