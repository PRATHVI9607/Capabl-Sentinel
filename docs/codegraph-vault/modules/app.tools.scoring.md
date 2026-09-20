---
tags: [codegraph, module, layer/tools]
layer: Tools
source: backend/app/tools/scoring.py
fan_in: 3
fan_out: 3
symbols: 7
community: 9
---

# `app.tools.scoring`

> Severity classification and the risk score.

Layer: [[Tools]] · `backend/app/tools/scoring.py` · 248 lines · 7 symbols

## Depends on

- [[app.llm]] — calls, imports ×2
- [[app.models]] — imports ×1
- [[app.models.risk]] — instantiates ×5

## Depended on by

- [[app.agents.nodes.risk_scorer]] — calls ×1
- [[app.tools]] — imports ×1
- [[app.tools.parsing]] — calls, imports ×3

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `_SeverityVerdict` | 88 |
| function | `tier_for` | 92 |
| function | `_contains` | 99 |
| function | `classify_severity_by_rules` | 103 |
| function | `classify_severity` | 126 |
| function | `compute_risk_score` | 151 |
| function | `score_incident` | 230 |

## External packages

`collections`, `logging`, `pydantic`, `re`
