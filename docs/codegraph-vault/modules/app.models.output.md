---
tags: [codegraph, module, layer/contracts]
layer: Contracts
source: backend/app/models/output.py
fan_in: 9
fan_out: 3
symbols: 8
community: -1
---

# `app.models.output`

> The payloads the API hands to the frontend.

Layer: [[Contracts]] · `backend/app/models/output.py` · 85 lines · 8 symbols

## Depends on

- [[app.models.incident]] — imports ×1
- [[app.models.retrieval]] — imports ×1
- [[app.models.risk]] — imports ×1

## Depended on by

- [[app.agents.nodes.error_handler]] — instantiates ×2
- [[app.agents.nodes.synthesis]] — instantiates ×2
- [[app.api.analyze]] — references ×1
- [[app.api.history]] — references ×2
- [[app.db.crud]] — instantiates ×2
- [[app.models]] — imports ×1
- [[app.pipeline]] — instantiates ×2
- [[app.stream]] — instantiates ×3
- [[app.tools.streaming]] — instantiates ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `_now` | 16 |
| class | `Urgency` | 20 |
| class | `Alert` | 26 |
| class | `CorrAction` | 36 |
| class | `AnalysisReport` | 43 |
| class | `AnalysisSummary` | 60 |
| class | `HistoryPage` | 72 |
| class | `StreamUpdate` | 79 |

## External packages

`datetime`, `enum`, `pydantic`, `uuid`
