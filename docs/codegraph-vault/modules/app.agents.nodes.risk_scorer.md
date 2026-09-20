---
tags: [codegraph, module, layer/orchestration]
layer: Orchestration
source: backend/app/agents/nodes/risk_scorer.py
fan_in: 2
fan_out: 7
symbols: 1
community: 10
---

# `app.agents.nodes.risk_scorer`

> Compute the risk score. Pure Python -- the LLM never touches this number.

Layer: [[Orchestration]] · `backend/app/agents/nodes/risk_scorer.py` · 37 lines · 1 symbols

## Depends on

- [[app.agents.nodes.base]] — calls, imports, instantiates ×3
- [[app.agents.state]] — imports ×1
- [[app.models]] — imports ×1
- [[app.tools]] — imports ×1
- [[app.tools.patterns]] — calls ×1
- [[app.tools.retrieval]] — calls ×2
- [[app.tools.scoring]] — calls ×1

## Depended on by

- [[app.agents.graph]] — imports ×1
- [[app.agents.nodes]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `risk_scorer` | 12 |
