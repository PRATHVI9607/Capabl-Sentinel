# Deployment

Backend to Render, frontend to Vercel. Both free tiers. Budget 25–35 minutes
end to end, most of it waiting on builds.

Do it in this order — the frontend needs the backend URL, and the backend needs
the frontend origin for CORS, so there is one deliberate loop back at step 4.

---

## Before you start

You need:

- The repo pushed to GitHub
- A Gemini API key — <https://aistudio.google.com> → "Get API key"
- A Groq API key — <https://console.groq.com> → API Keys
- Nothing else. No vector database, no Redis, no Postgres. The app runs on its
  bundled local index and a SQLite file unless you tell it otherwise.

**Rotate the two keys that were pasted into chat before you deploy.** They are
in a transcript. Generate fresh ones and use those below.

---

## 1. Push the repo

```bash
git add .
git commit -m "SENTINEL backend, corpus and docs"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

Check what you are about to publish first:

```bash
git status --short
git ls-files | grep -iE "\.env$|secret|credential"   # must print nothing
```

`.env`, `.claude/`, `.mcp.json`, `.codegraph/` and `node_modules/` are all
gitignored. `backend/data/vectors_*.npz`, `bm25_*.pkl`, `knowledge_graph.json`
and `corpus_manifest.json` **are** committed — those generated indexes are the
corpus the deployed app retrieves against. The source PDFs are not committed.

> If `corpus_manifest.json` does not exist yet, ingestion has not finished.
> Deploy anyway — see [Corpus](#6-corpus) below. The app starts fine without it.

---

## 2. Backend → Render

1. <https://dashboard.render.com> → **New** → **Web Service**
2. Connect the GitHub repo. Render reads `backend/render.yaml`, which already
   sets the root directory, build command, start command, health check and
   Python version. Accept them.
3. Plan: **Free**.
4. Set the two secrets under **Environment** (everything else is in the blueprint):

   | Key | Value |
   |---|---|
   | `GEMINI_API_KEY` | your key |
   | `GROQ_API_KEY` | your key |
   | `CORS_ORIGINS` | leave blank for now — step 4 fills it in |

5. **Create Web Service.** First build takes 5–10 minutes (fastembed and
   onnxruntime are the bulk of it; there is no PyTorch to install).

When it goes live, copy the URL — `https://sentinel-api-xxxx.onrender.com`.

**Verify before moving on:**

```bash
curl https://sentinel-api-xxxx.onrender.com/health
```

```json
{
  "status": "ok",
  "llm_configured": true,
  "vector_store_backend": "local",
  "vector_store_ready": true
}
```

- `llm_configured: false` → a key is missing or misspelled
- `vector_store_ready: false` → the indexes were not committed (see step 6)

---

## 3. Frontend → Vercel

1. <https://vercel.com/new> → import the same repo
2. **Root Directory: `frontend`** — this is the one setting Vercel will not
   infer. Framework (Next.js), build and output are auto-detected.
3. Environment variable:

   | Key | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://sentinel-api-xxxx.onrender.com` |

   No trailing slash.

4. **Deploy.** 2–4 minutes. Copy the URL — `https://your-app.vercel.app`.

---

## 4. Close the CORS loop

Back in Render → **Environment**:

| Key | Value |
|---|---|
| `CORS_ORIGINS` | `https://your-app.vercel.app` |

Comma-separate if you want previews too:
`https://your-app.vercel.app,http://localhost:3000`

Save. Render restarts automatically (~30s).

**Skipping this is the single most common deployment failure.** The API will
answer `curl` perfectly and the browser will show nothing, because the browser
enforces CORS and `curl` does not. Symptom: network tab shows the request
blocked, console says "No 'Access-Control-Allow-Origin' header".

---

## 5. Keep Render warm

Render's free tier sleeps after 15 minutes idle and takes ~50 seconds to wake.
That is a very long silence in a live demo.

1. <https://uptimerobot.com> → free account → **New Monitor**
2. Type **HTTP(s)**, URL `https://sentinel-api-xxxx.onrender.com/health`
3. Interval **14 minutes**

Do this the day before, not the hour before.

---

## 6. Corpus

Retrieval only works if the generated indexes are in the repo.

```bash
cd backend
python scripts/fetch_corpus.py       # ~26 CSB reports + 15 OSHA standards
python scripts/ingest_corpus.py      # chunk, embed, index, build the graph
python scripts/seed_regulatory.py
```

Ingestion takes roughly 45 minutes — the reports are 100+ page PDFs and every
sentence is embedded to find chunk boundaries. Then:

```bash
git add backend/data/vectors_* backend/data/bm25_* \
        backend/data/knowledge_graph.json backend/data/corpus_manifest.json
git commit -m "Add generated corpus indexes"
git push
```

Render redeploys automatically. `vector_store_ready` flips to `true`.

**Deploying before ingestion finishes is fine.** The app starts, accepts
uploads, extracts the incident, scores it and streams the pipeline. What it
cannot do is find similar historical incidents or cite regulatory clauses — both
lists come back empty and the report says so in `warnings`. Push the indexes
when they are ready and it fills in with no code change.

---

## 7. Verify end to end

```bash
API=https://sentinel-api-xxxx.onrender.com

curl -s $API/health | jq
curl -s $API/tools | jq 'length'                      # 10
curl -s "$API/history?limit=1" | jq '.total'          # 0 on a fresh deploy

curl -s -X POST $API/analyze -F "file=@some-report.pdf" | jq
# -> {"analysis_id": "...", "status": "processing"}

curl -N $API/analyze/<id>/stream                      # SSE, ends with "complete"
```

Then in the browser, on the Vercel URL:

- `/analyze` — drop a PDF, watch all seven pipeline nodes light up
- Risk card — the four components must sum to the total shown
- Regulatory clauses — each shows its source document
- `/dashboard`, `/incidents`, `/alerts` — render without errors
- Resize to 375px — no horizontal scroll

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Browser shows nothing, `curl` works | `CORS_ORIGINS` missing or has a trailing slash | Step 4 |
| `llm_configured: false` | Key missing on Render | Re-check Environment, redeploy |
| 404 from the model provider | Model retired | Defaults are floating aliases (`gemini-flash-latest`, `openai/gpt-oss-20b`); if you pinned a version, unpin it |
| `vector_store_ready: false` | Indexes not committed | Step 6 |
| Empty `similar_incidents` / `regulatory_clauses` | Same | Step 6 |
| First request takes ~50s | Free tier cold start | Step 5 |
| Build OOM on Render | `SPACY_MODEL` set to `en_core_web_lg` | Leave it as `blank` |
| 429 on upload | Rate limit, 10/IP/hour | Raise `MAX_ANALYSES_PER_IP_PER_HOUR` |
| SSE stream hangs | A proxy is buffering | The app already sends `X-Accel-Buffering: no`; check any proxy you added |

---

## Optional upgrades

None of these are needed to run.

**Postgres instead of SQLite.** SQLite on Render lives on ephemeral disk, so
history resets on every deploy. For persistence, create a Supabase project and
set `DATABASE_URL` to its pooled connection string with the asyncpg driver:

```
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@HOST:5432/postgres
```

Tables are created at startup.

**Shared cache.** With one instance the in-process cache is fine. For more than
one, create an Upstash Redis database and set `UPSTASH_REDIS_REST_URL` and
`UPSTASH_REDIS_REST_TOKEN` so the response cache and rate-limit counters are
shared.

**Qdrant.** Only worth it past roughly 100k chunks. Set `QDRANT_URL` and
`QDRANT_API_KEY`, add `pip install -r requirements-qdrant.txt` to the build
command, and re-run the ingest scripts so the collections get populated.

---

## What is deployed

```mermaid
flowchart LR
    U(["browser"]) -->|"HTTPS"| V["Vercel<br/>Next.js frontend"]
    V -->|"POST /analyze · SSE"| R["Render<br/>FastAPI + LangGraph"]
    R --> G["Gemini<br/>extraction · synthesis"]
    R --> Q["Groq<br/>fast classification"]
    R --> I[("local index<br/>vectors + BM25 + graph<br/>committed to the repo")]
    R --> D[("SQLite<br/>analysis history")]
    UR["UptimeRobot"] -.->|"/health every 14 min"| R

    classDef host fill:#16162A,stroke:#4F8EF7,color:#F0F0FA
    classDef ext fill:#1C1C34,stroke:#FFB800,color:#F0F0FA
    classDef store fill:#0F0F1A,stroke:#8888AA,color:#F0F0FA
    class V,R host
    class G,Q,UR ext
    class I,D store
```
