---
title: SENTINEL API
emoji: 🦺
colorFrom: blue
colorTo: red
sdk: gradio
sdk_version: 5.9.1
python_version: "3.11"
app_file: space_app.py
pinned: false
license: mit
short_description: Precursor detection over workplace safety incident reports
---

# SENTINEL — API

Backend for [SENTINEL](https://github.com/PRATHVI9607/Capabl-Sentinel): upload a
workplace safety incident report, get the precursor conditions it shares with
past investigations, the regulatory clauses that apply, and an explainable risk
score — streamed stage by stage.

This Space runs the FastAPI service only. The UI is deployed separately on
Vercel.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | liveness and configuration readout |
| `POST` | `/analyze` | upload a PDF, start an analysis |
| `GET` | `/analyze/{id}/stream` | server-sent events, one per pipeline stage |
| `GET` | `/analyze/{id}` | the finished report |
| `GET` | `/history` | completed analyses, paged and filterable |
| `GET` | `/tools` | the ten agent tools and their argument schemas |

Full contract: [`docs/API.md`](https://github.com/PRATHVI9607/Capabl-Sentinel/blob/main/docs/API.md)

## Configuration

Set these as **Repository secrets** in Space settings:

| Secret | Required | Notes |
|---|---|---|
| `GROQ_API_KEY` | yes | primary provider |
| `GEMINI_API_KEY` | recommended | fallback; its free tier is 20 requests/day |
| `CORS_ORIGINS` | yes | your frontend origin, comma-separated |

Everything else has a working default. No vector database, Redis or Postgres is
needed — the vector index ships in the image and SQLite handles history.

## What it does

Retrieval runs BM25 and dense vectors in parallel, fuses them with reciprocal
rank fusion, reranks with a cross-encoder, then trims each passage to the
sentences that earned the match — so every citation is traceable to its source
document.

The risk score is deterministic Python, not a model output: four weighted
components, each displayed with its weight, summing to the total. Regulatory
clauses are retrieved text rather than generated, so the system cannot invent a
citation.

Corpus: 26 US Chemical Safety Board investigation reports and 15 OSHA standards
pulled verbatim from the federal eCFR API. Both public domain.
