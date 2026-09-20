---
tags: [codegraph, module, layer/tools]
layer: Tools
source: backend/app/tools/patterns.py
fan_in: 4
fan_out: 5
symbols: 7
community: 11
---

# `app.tools.patterns`

> Precursor detection and causal chain traversal.

Layer: [[Tools]] · `backend/app/tools/patterns.py` · 145 lines · 7 symbols

## Depends on

- [[app.config]] — imports ×1
- [[app.knowledge_graph.graph]] — imports ×1
- [[app.knowledge_graph.serializer]] — calls, imports ×2
- [[app.models]] — imports ×1
- [[app.models.risk]] — instantiates ×3

## Depended on by

- [[app.agents.nodes.entity_extractor]] — calls ×1
- [[app.agents.nodes.pattern_detector]] — calls ×2
- [[app.agents.nodes.risk_scorer]] — calls ×1
- [[app.tools]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `PrecursorDefinition` | 23 |
| method | `matches` | 29 |
| function | `taxonomy` | 34 |
| function | `detect_hazard_type` | 52 |
| function | `known_precursor_count` | 64 |
| function | `detect_precursor_patterns` | 70 |
| function | `build_causal_chain` | 110 |

## External packages

`dataclasses`, `functools`, `json`
