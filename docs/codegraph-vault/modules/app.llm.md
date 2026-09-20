---
tags: [codegraph, module, layer/providers]
layer: Providers
source: backend/app/llm.py
fan_in: 6
fan_out: 1
symbols: 8
community: 9
---

# `app.llm`

> LLM access with a two-provider fallback.

Layer: [[Providers]] · `backend/app/llm.py` · 88 lines · 8 symbols

## Depends on

- [[app.config]] — imports ×1

## Depended on by

- [[app.agents.nodes.synthesis]] — calls, imports ×2
- [[app.api.health]] — calls, imports ×2
- [[app.ingest.classifier]] — calls, imports ×2
- [[app.tools.actions]] — calls, imports ×2
- [[app.tools.parsing]] — calls, imports ×4
- [[app.tools.scoring]] — calls, imports ×2

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `LLMUnavailable` | 26 |
| function | `_gemini` | 31 |
| function | `_groq` | 44 |
| function | `_providers` | 56 |
| function | `any_provider_configured` | 61 |
| function | `complete_structured` | 65 |
| function | `complete_text` | 70 |
| function | `_attempt` | 75 |

## External packages

`collections`, `functools`, `logging`, `pydantic`, `typing`
