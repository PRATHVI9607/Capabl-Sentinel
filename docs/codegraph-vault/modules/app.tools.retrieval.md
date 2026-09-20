---
tags: [codegraph, module, layer/tools]
layer: Tools
source: backend/app/tools/retrieval.py
fan_in: 4
fan_out: 4
symbols: 8
community: 8
---

# `app.tools.retrieval`

> Retrieval tools: historical incidents and applicable regulatory clauses.

Layer: [[Tools]] · `backend/app/tools/retrieval.py` · 155 lines · 8 symbols

## Depends on

- [[app.config]] — imports ×1
- [[app.models]] — imports ×1
- [[app.models.retrieval]] — instantiates ×2
- [[app.rag.retriever]] — calls, imports ×4

## Depended on by

- [[app.agents.nodes.pattern_detector]] — calls ×1
- [[app.agents.nodes.regulatory_auditor]] — calls ×2
- [[app.agents.nodes.risk_scorer]] — calls ×2
- [[app.tools]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `rank_confidence` | 51 |
| function | `corpus_size` | 57 |
| function | `clause_family` | 66 |
| function | `hybrid_search_incidents` | 75 |
| function | `_to_similar_incident` | 100 |
| function | `retrieve_regulatory_clauses` | 115 |
| function | `_to_clause` | 130 |
| function | `violated_clause_families` | 147 |

## External packages

`functools`, `json`, `logging`, `re`
