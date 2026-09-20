---
tags: [codegraph, module, layer/transport]
layer: Transport
source: backend/app/api/analyze.py
fan_in: 1
fan_out: 8
symbols: 7
community: 6
---

# `app.api.analyze`

> Upload, stream, and fetch a single analysis.

Layer: [[Transport]] · `backend/app/api/analyze.py` · 123 lines · 7 symbols

## Depends on

- [[app.cache.client]] — imports ×1
- [[app.config]] — imports ×1
- [[app.db.crud]] — calls, imports ×3
- [[app.deps]] — imports ×1
- [[app.models]] — imports ×1
- [[app.models.output]] — references ×1
- [[app.pipeline]] — calls, imports, references ×3
- [[app.stream]] — calls, imports ×3

## Depended on by

- [[app.main]] — imports ×1

## Symbols

| Kind | Name | Line |
|---|---|---|
| function | `safe_filename` | 37 |
| function | `read_capped` | 48 |
| function | `validate` | 67 |
| function | `start_analysis` | 77 |
| function | `stream_analysis` | 107 |
| function | `events` | 110 |
| function | `get_analysis` | 118 |

## External packages

`fastapi`, `hashlib`, `pathlib`, `re`, `tempfile`, `uuid`
