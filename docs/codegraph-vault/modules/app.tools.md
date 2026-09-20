---
tags: [codegraph, module, layer/tools]
layer: Tools
source: backend/app/tools/__init__.py
fan_in: 9
fan_out: 6
symbols: 2
community: 9
---

# `app.tools`

> The ten SENTINEL tools.

Layer: [[Tools]] · `backend/app/tools/__init__.py` · 87 lines · 2 symbols

## Depends on

- [[app.tools.actions]] — imports ×1
- [[app.tools.parsing]] — imports ×1
- [[app.tools.patterns]] — imports ×1
- [[app.tools.retrieval]] — imports ×1
- [[app.tools.scoring]] — imports ×1
- [[app.tools.streaming]] — imports ×1

## Depended on by

- [[app.agents.nodes.base]] — imports ×1
- [[app.agents.nodes.entity_extractor]] — imports ×1
- [[app.agents.nodes.error_handler]] — imports ×1
- [[app.agents.nodes.incident_parser]] — imports ×1
- [[app.agents.nodes.pattern_detector]] — imports ×1
- [[app.agents.nodes.regulatory_auditor]] — imports ×1
- [[app.agents.nodes.risk_scorer]] — imports ×1
- [[app.agents.nodes.synthesis]] — imports ×1
- [[app.api.tools]] — calls, imports ×2

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `_as_tool` | 53 |
| function | `tool_registry` | 63 |

## External packages

`functools`, `langchain_core`
