---
tags: [codegraph, layer]
---

# Transport

7 modules. Layer 5 of 6; imports may point down this list, never up.

| Module | In | Out | Symbols | Purpose |
|---|---|---|---|---|
| [[app.api]] | 0 | 0 | 0 | HTTP routes. No business logic lives here. |
| [[app.api.analyze]] | 1 | 8 | 7 | Upload, stream, and fetch a single analysis. |
| [[app.api.health]] | 1 | 4 | 1 | Liveness endpoint. Also the UptimeRobot target that keeps Render warm. |
| [[app.api.history]] | 1 | 4 | 3 | Past analyses: the list behind the incident explorer and the dashboard stats. |
| [[app.api.tools]] | 1 | 1 | 2 | Introspection over the agent's tool set. |
| [[app.deps]] | 2 | 1 | 0 | FastAPI dependencies. |
| [[app.main]] | 0 | 8 | 4 | FastAPI application: CORS, rate limiting, security headers, routes, startup. |
