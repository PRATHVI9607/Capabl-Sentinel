---
tags: [codegraph, layer]
---

# Contracts

6 modules. Layer 0 of 6; imports may point down this list, never up.

| Module | In | Out | Symbols | Purpose |
|---|---|---|---|---|
| [[app.config]] | 20 | 0 | 3 | Process-wide configuration, read once from the environment. |
| [[app.models]] | 18 | 4 | 0 | Pydantic models — the single source of truth for every shape in the system. |
| [[app.models.incident]] | 5 | 0 | 4 | Structured representation of a parsed safety incident. |
| [[app.models.output]] | 9 | 3 | 8 | The payloads the API hands to the frontend. |
| [[app.models.retrieval]] | 4 | 0 | 3 | Models for everything that comes back out of the retrieval layer. |
| [[app.models.risk]] | 5 | 1 | 4 | Risk scoring output. The numbers here come from pure Python, never an LLM. |
