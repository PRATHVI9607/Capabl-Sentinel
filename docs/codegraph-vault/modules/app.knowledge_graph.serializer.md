---
tags: [codegraph, module, layer/retrieval]
layer: Retrieval
source: backend/app/knowledge_graph/serializer.py
fan_in: 1
fan_out: 1
symbols: 3
community: 11
---

# `app.knowledge_graph.serializer`

> Persist the knowledge graph as JSON on disk.

Layer: [[Retrieval]] · `backend/app/knowledge_graph/serializer.py` · 52 lines · 3 symbols

## Depends on

- [[app.config]] — imports ×1

## Depended on by

- [[app.tools.patterns]] — calls, imports ×2

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `graph_path` | 30 |
| function | `save` | 34 |
| function | `load` | 44 |

## External packages

`functools`, `inspect`, `json`, `logging`, `networkx`, `pathlib`
