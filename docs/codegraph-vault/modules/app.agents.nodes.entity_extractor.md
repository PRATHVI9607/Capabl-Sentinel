---
tags: [codegraph, module, layer/orchestration]
layer: Orchestration
source: backend/app/agents/nodes/entity_extractor.py
fan_in: 2
fan_out: 6
symbols: 1
community: 10
---

# `app.agents.nodes.entity_extractor`

> Pull hazard entities out of the text and settle on a hazard family.

Layer: [[Orchestration]] · `backend/app/agents/nodes/entity_extractor.py` · 31 lines · 1 symbols

## Depends on

- [[app.agents.nodes.base]] — calls, imports, instantiates ×3
- [[app.agents.state]] — imports ×1
- [[app.models]] — imports ×1
- [[app.tools]] — imports ×1
- [[app.tools.parsing]] — calls ×1
- [[app.tools.patterns]] — calls ×1

## Depended on by

- [[app.agents.graph]] — imports ×1
- [[app.agents.nodes]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `entity_extractor` | 12 |
