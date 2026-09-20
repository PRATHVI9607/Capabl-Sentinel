---
tags: [codegraph, layer]
---

# Providers

8 modules. Layer 1 of 6; imports may point down this list, never up.

| Module | In | Out | Symbols | Purpose |
|---|---|---|---|---|
| [[app.cache]] | 0 | 0 | 0 | Response cache and rate-limit counters. |
| [[app.cache.client]] | 3 | 1 | 7 | Key/value cache over the Upstash REST API, with an in-process fallback. |
| [[app.db]] | 0 | 0 | 0 | Persistence layer: engine, tables, queries. |
| [[app.db.crud]] | 3 | 4 | 6 | Every read and write against the analyses table. |
| [[app.db.models]] | 2 | 0 | 2 | SQLAlchemy tables. One row per analysis; the report itself is stored as JSON. |
| [[app.db.session]] | 3 | 2 | 2 | Async engine and session factory. |
| [[app.llm]] | 6 | 1 | 8 | LLM access with a two-provider fallback. |
| [[app.stream]] | 3 | 3 | 9 | In-process pub/sub between the analysis background task and SSE subscribers. |
