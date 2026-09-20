---
tags: [codegraph, module, layer/transport]
layer: Transport
source: backend/app/api/tools.py
fan_in: 1
fan_out: 1
symbols: 2
community: 9
---

# `app.api.tools`

> Introspection over the agent's tool set.

Layer: [[Transport]] · `backend/app/api/tools.py` · 32 lines · 2 symbols

## Depends on

- [[app.tools]] — calls, imports ×2

## Depended on by

- [[app.main]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `ToolDescription` | 13 |
| function | `list_tools` | 21 |

## External packages

`fastapi`, `pydantic`
