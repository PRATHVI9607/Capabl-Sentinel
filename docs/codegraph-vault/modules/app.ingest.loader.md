---
tags: [codegraph, module, layer/retrieval]
layer: Retrieval
source: backend/app/ingest/loader.py
fan_in: 1
fan_out: 1
symbols: 3
community: 6
---

# `app.ingest.loader`

> PDF text extraction: pdfplumber first, OCR only if the page layer is empty.

Layer: [[Retrieval]] · `backend/app/ingest/loader.py` · 85 lines · 3 symbols

## Depends on

- [[app.config]] — imports ×1

## Depended on by

- [[app.pipeline]] — imports, references ×2

## Symbols

| Kind | Name | Line |
|---|---|---|
| class | `DocumentLoadError` | 18 |
| function | `load_pdf` | 22 |
| function | `_ocr` | 72 |

## External packages

`logging`, `pathlib`, `pdfplumber`
