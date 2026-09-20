---
tags: [codegraph, module, layer/tools]
layer: Tools
source: backend/app/tools/actions.py
fan_in: 2
fan_out: 3
symbols: 6
community: 9
---

# `app.tools.actions`

> Corrective action generation.

Layer: [[Tools]] · `backend/app/tools/actions.py` · 102 lines · 6 symbols

## Depends on

- [[app.config]] — imports ×1
- [[app.llm]] — calls, imports ×2
- [[app.models]] — imports ×1

## Depended on by

- [[app.agents.nodes.synthesis]] — calls ×1
- [[app.tools]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `_GeneratedActions` | 27 |
| function | `_templates` | 32 |
| function | `sort_by_urgency` | 37 |
| function | `generate_corrective_actions` | 41 |
| function | `_deduplicate` | 59 |
| function | `_generate` | 70 |

## External packages

`functools`, `json`, `logging`, `pydantic`
