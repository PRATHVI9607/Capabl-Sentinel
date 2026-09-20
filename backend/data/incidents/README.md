# Historical incident corpus

Populated automatically:

```bash
python scripts/fetch_corpus.py    # downloads CSB investigation reports here
python scripts/ingest_corpus.py   # chunks, embeds and indexes them
```

To add documents by hand, drop PDFs or plain `.txt` files in this directory and
re-run the ingest script.

The file name becomes the incident title in the UI, so name files descriptively
(`2019-08-12 Refinery hydrocarbon release.pdf`, not `doc1.pdf`).

## Where to get them — all free, all public domain

| Source | What | Target count | URL |
|---|---|---|---|
| OSHA IMIS Accident Investigation Search | Fatality/catastrophe investigation summaries | 40 | <https://www.osha.gov/ords/imis/accidentsearch.html> |
| CSB investigation reports | Chemical process safety investigations | 15 | <https://www.csb.gov/investigations/> |
| NIOSH FACE program | Fatality Assessment and Control Evaluation case studies | 15 | <https://www.cdc.gov/niosh/face/> |
| UK HSE | Investigation and enforcement reports | 10 | <https://www.hse.gov.uk/> |

**Target: 80 documents.** The pipeline runs with fewer, but the frequency
component of the risk score and the precursor evidence counts both get weaker
as the corpus shrinks — `corpus_manifest.json` records what was actually
ingested so the numbers stay honest.

## Notes

- Scanned PDFs with no text layer need the optional OCR extra
  (`pip install -r requirements-ocr.txt`); without it they are skipped with a
  warning rather than silently producing empty chunks.
- These files are not committed by default. See `.gitignore` — commit them if
  you want the corpus reproducible from a clone, or keep them local and rely on
  the Qdrant collection persisting.
