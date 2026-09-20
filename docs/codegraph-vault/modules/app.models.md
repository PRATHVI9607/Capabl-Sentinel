---
tags: [codegraph, module, layer/contracts]
layer: Contracts
source: backend/app/models/__init__.py
fan_in: 18
fan_out: 4
symbols: 0
community: -1
---

# `app.models`

> Pydantic models — the single source of truth for every shape in the system.

Layer: [[Contracts]] · `backend/app/models/__init__.py` · 36 lines · 0 symbols

## Depends on

- [[app.models.incident]] — imports ×1
- [[app.models.output]] — imports ×1
- [[app.models.retrieval]] — imports ×1
- [[app.models.risk]] — imports ×1

## Depended on by

- [[app.agents.nodes.entity_extractor]] — imports ×1
- [[app.agents.nodes.error_handler]] — imports ×1
- [[app.agents.nodes.pattern_detector]] — imports ×1
- [[app.agents.nodes.regulatory_auditor]] — imports ×1
- [[app.agents.nodes.risk_scorer]] — imports ×1
- [[app.agents.nodes.synthesis]] — imports ×1
- [[app.api.analyze]] — imports ×1
- [[app.api.history]] — imports ×1
- [[app.db.crud]] — imports ×1
- [[app.pipeline]] — imports ×1
- [[app.rag.retriever]] — imports ×1
- [[app.stream]] — imports ×1
- [[app.tools.actions]] — imports ×1
- [[app.tools.parsing]] — imports ×1
- [[app.tools.patterns]] — imports ×1
- [[app.tools.retrieval]] — imports ×1
- [[app.tools.scoring]] — imports ×1
- [[app.tools.streaming]] — imports ×1
