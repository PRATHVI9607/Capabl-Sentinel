---
tags: [codegraph, module, layer/contracts]
layer: Contracts
source: backend/app/models/risk.py
fan_in: 5
fan_out: 1
symbols: 4
community: -1
---

# `app.models.risk`

> Risk scoring output. The numbers here come from pure Python, never an LLM.

Layer: [[Contracts]] · `backend/app/models/risk.py` · 37 lines · 4 symbols

## Depends on

- [[app.models.incident]] — imports ×1

## Depended on by

- [[app.agents.nodes.error_handler]] — instantiates ×2
- [[app.models]] — imports ×1
- [[app.models.output]] — imports ×1
- [[app.tools.patterns]] — instantiates ×3
- [[app.tools.scoring]] — instantiates ×5

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `RiskComponent` | 10 |
| class | `PrecursorPattern` | 17 |
| class | `CausalEvent` | 25 |
| class | `RiskScore` | 32 |

## External packages

`pydantic`
