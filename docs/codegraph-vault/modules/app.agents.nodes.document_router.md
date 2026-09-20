---
tags: [codegraph, module, layer/orchestration]
layer: Orchestration
source: backend/app/agents/nodes/document_router.py
fan_in: 2
fan_out: 4
symbols: 1
community: 10
---

# `app.agents.nodes.document_router`

> Decide what was uploaded and flag documents the pipeline cannot do much with.

Layer: [[Orchestration]] · `backend/app/agents/nodes/document_router.py` · 37 lines · 1 symbols

## Depends on

- [[app.agents.nodes.base]] — calls, imports, instantiates ×3
- [[app.agents.state]] — imports ×1
- [[app.config]] — imports ×1
- [[app.ingest.classifier]] — calls, imports ×2

## Depended on by

- [[app.agents.graph]] — imports ×1
- [[app.agents.nodes]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `document_router` | 18 |
