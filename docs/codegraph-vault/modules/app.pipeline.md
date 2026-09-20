---
tags: [codegraph, module, layer/orchestration]
layer: Orchestration
source: backend/app/pipeline.py
fan_in: 1
fan_out: 11
symbols: 4
community: 6
---

# `app.pipeline`

> One analysis, end to end: PDF in, persisted AnalysisReport out.

Layer: [[Orchestration]] · `backend/app/pipeline.py` · 95 lines · 4 symbols

## Depends on

- [[app.agents.graph]] — calls, imports ×2
- [[app.agents.state]] — calls, imports ×2
- [[app.cache.client]] — imports ×1
- [[app.config]] — imports ×1
- [[app.db.crud]] — calls, imports ×3
- [[app.db.session]] — calls, imports ×3
- [[app.ingest.loader]] — imports, references ×2
- [[app.ingest.preprocessor]] — calls, imports ×2
- [[app.models]] — imports ×1
- [[app.models.output]] — instantiates ×2
- [[app.stream]] — calls, imports ×3

## Depended on by

- [[app.api.analyze]] — calls, imports, references ×3

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `cache_key` | 35 |
| function | `run_analysis` | 39 |
| function | `_analyse` | 76 |
| function | `_fail` | 90 |

## External packages

`asyncio`, `logging`, `pathlib`, `time`
