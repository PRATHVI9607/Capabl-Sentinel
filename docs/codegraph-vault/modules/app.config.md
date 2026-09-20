---
tags: [codegraph, module, layer/contracts]
layer: Contracts
source: backend/app/config.py
fan_in: 20
fan_out: 0
symbols: 3
community: -1
---

# `app.config`

> Process-wide configuration, read once from the environment.

Layer: [[Contracts]] · `backend/app/config.py` · 82 lines · 3 symbols

## Depends on

_Nothing in this package._

## Depended on by

- [[app.agents.nodes.document_router]] — imports ×1
- [[app.api.analyze]] — imports ×1
- [[app.api.health]] — imports ×1
- [[app.cache.client]] — imports ×1
- [[app.db.session]] — imports ×1
- [[app.ingest.loader]] — imports ×1
- [[app.knowledge_graph.serializer]] — imports ×1
- [[app.llm]] — imports ×1
- [[app.main]] — imports ×1
- [[app.pipeline]] — imports ×1
- [[app.rag.embedder]] — imports ×1
- [[app.rag.local_store]] — imports ×1
- [[app.rag.qdrant_store]] — imports ×1
- [[app.rag.retriever]] — imports ×1
- [[app.rag.vector_store]] — imports ×1
- [[app.stream]] — imports ×1
- [[app.tools.actions]] — imports ×1
- [[app.tools.parsing]] — imports ×1
- [[app.tools.patterns]] — imports ×1
- [[app.tools.retrieval]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `Settings` | 12 |
| method | `is_production` | 73 |
| method | `cors_origin_list` | 77 |

## External packages

`pathlib`, `pydantic_settings`
