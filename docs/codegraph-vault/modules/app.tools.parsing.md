---
tags: [codegraph, module, layer/tools]
layer: Tools
source: backend/app/tools/parsing.py
fan_in: 3
fan_out: 5
symbols: 13
community: 9
---

# `app.tools.parsing`

> Turn raw report text into an IncidentReport and a list of hazard entities.

Layer: [[Tools]] · `backend/app/tools/parsing.py` · 295 lines · 13 symbols

## Depends on

- [[app.config]] — imports ×1
- [[app.llm]] — calls, imports ×4
- [[app.models]] — imports ×1
- [[app.models.incident]] — instantiates ×4
- [[app.tools.scoring]] — calls, imports ×3

## Depended on by

- [[app.agents.nodes.entity_extractor]] — calls ×1
- [[app.agents.nodes.incident_parser]] — calls ×1
- [[app.tools]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `_Verification` | 43 |
| class | `_DiscoveredEntity` | 49 |
| class | `_EntityDiscovery` | 54 |
| class | `_ParsedIncident` | 58 |
| function | `parse_incident_report` | 72 |
| function | `_extraction_confidence` | 99 |
| function | `_nlp` | 120 |
| function | `_patterns` | 161 |
| function | `spacy_entities` | 165 |
| function | `_entity_type` | 190 |
| function | `extract_hazard_entities` | 196 |
| function | `_verify_uncertain` | 212 |
| function | `_discover_missing` | 249 |

## External packages

`asyncio`, `functools`, `json`, `logging`, `pydantic`
