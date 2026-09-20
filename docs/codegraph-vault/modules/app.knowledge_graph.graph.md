---
tags: [codegraph, module, layer/retrieval]
layer: Retrieval
source: backend/app/knowledge_graph/graph.py
fan_in: 1
fan_out: 0
symbols: 6
community: 11
---

# `app.knowledge_graph.graph`

> NetworkX causal graph over the historical corpus.

Layer: [[Retrieval]] · `backend/app/knowledge_graph/graph.py` · 101 lines · 6 symbols

## Depends on

_Nothing in this package._

## Depended on by

- [[app.tools.patterns]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `ChainStep` | 23 |
| function | `new_graph` | 30 |
| function | `node_key` | 34 |
| function | `add_incident` | 38 |
| function | `link_precursor` | 67 |
| function | `find_precursor_chain` | 71 |

## External packages

`dataclasses`, `networkx`
