---
tags: [codegraph, module, layer/orchestration]
layer: Orchestration
source: backend/app/agents/nodes/pattern_detector.py
fan_in: 2
fan_out: 6
symbols: 2
community: 10
---

# `app.agents.nodes.pattern_detector`

> Find historical matches, then the precursor patterns they corroborate.

Layer: [[Orchestration]] · `backend/app/agents/nodes/pattern_detector.py` · 47 lines · 2 symbols

## Depends on

- [[app.agents.nodes.base]] — calls, imports, instantiates ×3
- [[app.agents.state]] — imports ×1
- [[app.models]] — imports ×1
- [[app.tools]] — imports ×1
- [[app.tools.patterns]] — calls ×2
- [[app.tools.retrieval]] — calls ×1

## Depended on by

- [[app.agents.graph]] — imports ×1
- [[app.agents.nodes]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `_search_query` | 14 |
| function | `pattern_detector` | 22 |
