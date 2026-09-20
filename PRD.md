# SENTINEL — Safety ENTRy INcident Threat Early-warning Layer
### PRD v1.0 | Hackathon Edition | Track C3

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Hackathon Scoring Checklist](#2-hackathon-scoring-checklist)
3. [System Architecture](#3-system-architecture)
4. [Tech Stack — Full Install Reference](#4-tech-stack--full-install-reference)
5. [Project Folder Structure](#5-project-folder-structure)
6. [Environment Variables](#6-environment-variables)
7. [Data Corpus Setup](#7-data-corpus-setup)
8. [Backend Implementation](#8-backend-implementation)
9. [Frontend Implementation](#9-frontend-implementation)
10. [API Reference](#10-api-reference)
11. [Clean Code Rules](#11-clean-code-rules)
12. [Deployment Guide](#12-deployment-guide)
13. [Testing Checklist](#13-testing-checklist)
14. [Demo Script](#14-demo-script)

---

## 1. Project Overview

**Name:** SENTINEL
**Full form:** Safety ENTRy INcident Threat Early-warning Layer
**Track:** C3 — Safety Report Analysis Agent (Incident Precursor Detector)
**Core value prop:** Upload any safety incident report. SENTINEL extracts structured entities, detects recurring precursor patterns across 80+ real historical cases, cross-references applicable regulations via hybrid RAG, computes a multi-dimensional risk score with a custom Python algorithm, and streams structured alerts with prioritized corrective actions — all in under 45 seconds.

**What makes it different from basic RAG:**
- Hybrid retrieval: BM25 + Qdrant dense + RRF merge + FlashRank cross-encoder reranking
- LangGraph typed state machine with conditional edges, not a sequential chain
- 10 real Python tools with custom algorithms — no LLM guessing
- Live SSE streaming per agent node — UI shows the pipeline running in real time
- NetworkX knowledge graph for causal chain traversal
- Pre-loaded corpus of 80 real OSHA / CSB / NIOSH incident reports
- Dual LLM strategy: Gemini 2.0 Flash (1M TPM) for reasoning, Groq llama-3.1-8b (131k TPM) for fast tool calls

**Tagline for judges:** "Not just analysis — precursor detection. It finds the warning signs before the next accident happens."

---

## 2. Hackathon Scoring Checklist

### Creativity (100 pts)

**Visual / UX Design (40)**
- [ ] Custom dark dashboard — not a default template. Zero generic AI aesthetics.
- [ ] Severity-coded color system: CRITICAL (red) / HIGH (orange) / MEDIUM (yellow) / LOW (green)
- [ ] Animated risk gauge: SVG semicircle arc + framer-motion spring-animated needle
- [ ] Pipeline visualization: 7 agent nodes with live SSE-driven state (idle / active pulse / complete / error)
- [ ] Regulatory citation cards with collapse/expand and confidence badge
- [ ] Causal chain timeline component

**Beyond-Chat Interaction (30)**
- [ ] Drag-and-drop file upload zone (react-dropzone) — no chat interface
- [ ] Real-time SSE pipeline progress: each agent node activates + completes visually
- [ ] Interactive risk gauge (animated on result load)
- [ ] Filterable incident explorer: industry tabs + severity filter
- [ ] Collapsible regulatory clause cards with source citation
- [ ] Corrective action list with urgency tiers: IMMEDIATE / SHORT-TERM / LONG-TERM
- [ ] "Try a sample report" CTA with pre-loaded OSHA PDF

**Polish & Delight (30)**
- [ ] Skeleton loading per section — not a full-page spinner
- [ ] SSE stream shows agent name + live status message
- [ ] Empty state: descriptive CTA with sample report button
- [ ] Error state: clear message + retry button, no crash
- [ ] CRITICAL alert pulse animation (box-shadow breathing loop)
- [ ] Toast notifications for upload success / failure (sonner)

### Problem Relevance (100 pts)

**Problem-Market Fit (40)**
- India reported 48,000+ factory accidents in 2022 (DGFASLI Annual Report — cite in README)
- Target users: safety officers, DGFASLI inspectors, EHS compliance managers, factory auditors
- Real workflow: upload internal or OSHA report → get structured risk assessment → share PDF summary

**Originality (30)**
- "Precursor detection" framing: predicts what will happen next, not just categorizes what happened
- Pattern mining across 80+ real historical cases — most teams will have zero corpus
- Multi-dimensional risk score with explainable components: judges see the math behind the number

**Practical Usability (30)**
- Upload → analyze → result in under 45 seconds
- Download PDF summary button for sharing
- Mobile-responsive layout (test at 375px)

### Technical (100 pts)

**Pipeline Completeness (20)**
- [ ] pdfplumber loaders + unstructured OCR fallback
- [ ] Semantic chunking (similarity-threshold, not fixed character size)
- [ ] bge-small-en-v1.5 embeddings (67MB, fits Render free tier RAM)
- [ ] Qdrant Cloud vector store (3 separate collections)
- [ ] Hybrid retriever: BM25 + dense + RRF + FlashRank

**RAG Quality (20)**
- [ ] Every answer traceable to exact retrieved chunk
- [ ] Source citations shown in UI: document name + section + chunk excerpt
- [ ] FlashRank reranking ensures precision over recall
- [ ] Contextual compression trims irrelevant portions of retrieved docs
- [ ] Zero hallucinated regulatory citations — every clause is retrieved, not generated

**Tool Design & Tool Calling (25)**
- [ ] 10 `@tool` decorated functions with real Python logic
- [ ] All tools have precise docstrings (LangGraph uses these for routing)
- [ ] Tools return typed Pydantic v2 models — no raw dicts
- [ ] Tool errors caught + re-routed to error_handler node, not propagated

**Agent Reasoning & Orchestration (25)**
- [ ] LangGraph TypedDict state (`SentinelState`) passed between every node
- [ ] Conditional edge: CRITICAL path vs STANDARD path after risk_scorer
- [ ] Multi-step: extract → retrieve → pattern match → score → alert
- [ ] Knowledge graph traversal in causal chain tool
- [ ] Max iteration guard (iteration_count <= 5 enforced in graph config)

**Live Correctness (10)**
- [ ] App runs end to end on a real OSHA PDF
- [ ] Non-PDF upload handled gracefully with clear error
- [ ] Empty / corrupt PDF handled — no 500 crash
- [ ] Gemini rate limit handled via Redis cache fallback
- [ ] Very short doc (< 100 words): returns low-confidence warning, not garbage output

---

## 3. System Architecture

```
USER BROWSER (Vercel)
  Next.js 14 App Router
  Upload Zone → Pipeline Visual → Risk Dashboard → Incident Explorer
        |
        | POST /analyze (multipart PDF)
        | GET  /analyze/{id}/stream  (SSE)
        |
BACKEND (Render.com)
  FastAPI + uvicorn
        |
  ┌─────────────────────────────────────────────────────┐
  │  L1: INGESTION                                       │
  │  pdfplumber (primary) → unstructured OCR (fallback) │
  │  Document type classifier (LLM)                      │
  └───────────────────┬─────────────────────────────────┘
                      ↓
  ┌─────────────────────────────────────────────────────┐
  │  L2: PROCESSING                                      │
  │  Semantic chunking (similarity-threshold splits)     │
  │  Hierarchical: doc → section → paragraph             │
  │  Metadata: date / industry / location / severity     │
  │  spaCy NER → LLM verification for low confidence     │
  │  NetworkX knowledge graph: incident→equipment→hazard │
  └───────────────────┬─────────────────────────────────┘
                      ↓
  ┌─────────────────────────────────────────────────────┐
  │  L3: MULTI-INDEX QDRANT                              │
  │  Index A: Historical incidents (80 OSHA/CSB/NIOSH)   │
  │  Index B: Regulatory corpus (OSHA/EPA/Factories Act) │
  │  Index C: Corrective actions database                │
  │  Dual encoding: bge-small-en-v1.5 + BM25             │
  └───────────────────┬─────────────────────────────────┘
                      ↓
  ┌─────────────────────────────────────────────────────┐
  │  L4: HYBRID RETRIEVAL                                │
  │  BM25 sparse  ║  Qdrant dense  → run in parallel    │
  │  Reciprocal Rank Fusion (RRF) score merge            │
  │  FlashRank cross-encoder reranking (top-k precision) │
  │  Metadata filter: industry + hazard_type + severity  │
  │  Contextual compression: strip irrelevant sentences  │
  └───────────────────┬─────────────────────────────────┘
                      ↓
  ┌─────────────────────────────────────────────────────┐
  │  L5: LANGGRAPH AGENT STATE MACHINE                   │
  │                                                      │
  │  document_router → incident_parser                   │
  │    → entity_extractor → pattern_detector             │
  │    → regulatory_auditor → risk_scorer                │
  │    → [conditional]                                   │
  │       score >= 8  → priority_alert_synthesizer       │
  │       score < 8   → alert_synthesizer                │
  │    → END                                             │
  │                                                      │
  │  error_handler connected to every node               │
  │  max_iterations = 5 guard                            │
  └───────────────────┬─────────────────────────────────┘
                      ↓
  ┌─────────────────────────────────────────────────────┐
  │  L6: OUTPUT                                          │
  │  SSE stream → frontend (StreamUpdate per node)       │
  │  Structured JSON: alert + risk_score + citations     │
  │  Supabase PostgreSQL: audit trail (every analysis)   │
  │  Upstash Redis: SHA256 cache (1hr TTL)               │
  └─────────────────────────────────────────────────────┘

EXTERNAL SERVICES
  Gemini 2.0 Flash  — LLM reasoning + synthesis (1M TPM free)
  Groq llama-3.1-8b — Fast tool calls (131k TPM free)
  Qdrant Cloud      — Vector store (1GB free cluster)
  Supabase          — PostgreSQL (500MB free)
  Upstash Redis     — Cache (10k cmds/day free)
```

**Risk Score Formula (pure Python, deterministic):**
```
R = (0.30 × severity_score)      # 0-10, from severity classifier
  + (0.25 × frequency_score)     # similar_incident_count / corpus_size, normalized 0-10
  + (0.25 × regulatory_score)    # sum(clause_weights for violated clauses), normalized 0-10
  + (0.20 × precursor_density)   # detected_precursors / known_precursors_for_hazard_type × 10

Thresholds:
  CRITICAL  R >= 8.0
  HIGH      6.0 <= R < 8.0
  MEDIUM    4.0 <= R < 6.0
  LOW       R < 4.0
```

**LLM Routing Strategy:**
```
Tool calls (fast, frequent)     → Groq llama-3.1-8b-instant (131k TPM, near-zero latency)
Reasoning + synthesis           → Gemini 2.0 Flash (1M TPM, generous free)
Rate limit fallback             → Swap to the other model via LangGraph retry edge
Cache hit                       → Neither model called, instant response
```

---

## 4. Tech Stack — Full Install Reference

### Backend Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install \
  fastapi==0.111.0 \
  "uvicorn[standard]==0.30.0" \
  python-multipart==0.0.9 \
  pydantic==2.7.0 \
  pydantic-settings==2.3.0 \
  langchain==0.2.6 \
  langgraph==0.2.0 \
  langchain-google-genai==1.0.7 \
  langchain-groq==0.1.6 \
  langchain-community==0.2.6 \
  sentence-transformers==3.0.1 \
  qdrant-client==1.9.1 \
  rank-bm25==0.2.2 \
  flashrank==0.2.8 \
  spacy==3.7.5 \
  pdfplumber==0.11.1 \
  "unstructured[pdf]==0.14.6" \
  networkx==3.3 \
  redis==5.0.6 \
  supabase==2.5.0 \
  sqlalchemy==2.0.31 \
  httpx==0.27.0 \
  "python-jose[cryptography]==3.3.0" \
  google-generativeai==0.7.2

# spaCy model — run once, Render caches it after first build
python -m spacy download en_core_web_lg

# Dev tools
pip install pytest pytest-asyncio black ruff
```

**requirements.txt** (pin exactly for reproducibility):
```
fastapi==0.111.0
uvicorn[standard]==0.30.0
python-multipart==0.0.9
pydantic==2.7.0
pydantic-settings==2.3.0
langchain==0.2.6
langgraph==0.2.0
langchain-google-genai==1.0.7
langchain-groq==0.1.6
langchain-community==0.2.6
sentence-transformers==3.0.1
qdrant-client==1.9.1
rank-bm25==0.2.2
flashrank==0.2.8
spacy==3.7.5
pdfplumber==0.11.1
unstructured[pdf]==0.14.6
networkx==3.3
redis==5.0.6
supabase==2.5.0
sqlalchemy==2.0.31
httpx==0.27.0
python-jose[cryptography]==3.3.0
google-generativeai==0.7.2
```

**Render build command:**
```
pip install -r requirements.txt && python -m spacy download en_core_web_lg
```

**Render start command:**
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

### Frontend Setup

```bash
npx create-next-app@14 sentinel-frontend \
  --typescript --tailwind --app --src-dir=false --import-alias="@/*"
cd sentinel-frontend

npm install \
  framer-motion@11 \
  recharts@2 \
  @tanstack/react-query@5 \
  zustand@4 \
  react-dropzone@14 \
  zod@3 \
  react-hook-form@7 \
  @hookform/resolvers@3 \
  clsx@2 \
  tailwind-merge@2 \
  class-variance-authority@0.7 \
  lucide-react \
  sonner \
  date-fns@3

# shadcn/ui init: choose dark theme + CSS variables when prompted
npx shadcn@latest init

# shadcn components
npx shadcn@latest add \
  button card badge dialog tabs progress \
  skeleton toast sheet command tooltip separator collapsible
```

**Aceternity UI — https://ui.aceternity.com/components (free, MIT)**
Copy component `.tsx` files from the site into `components/aceternity/`:
- `background-beams.tsx` — upload zone background
- `spotlight.tsx` — CRITICAL alert card highlight
- `hover-border-gradient.tsx` — primary CTA button wrapper
- `background-gradient.tsx` — risk score card outer glow
- `text-generate-effect.tsx` — "Analysis Complete" heading reveal
- `meteors.tsx` — subtle dashboard background

**Magic UI — https://magicui.design (free, MIT)**
Copy component `.tsx` files from the site into `components/magicui/`:
- `number-ticker.tsx` — stat card metrics + risk score counter
- `shimmer-button.tsx` — "Download PDF" secondary button
- `border-beam.tsx` — active analysis card animated border
- `animated-shiny-text.tsx` — CRITICAL severity badge text

Both libraries require only `framer-motion` and `clsx` as peer deps — already installed.

---

## 5. Project Folder Structure

```
sentinel/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app, CORS, router registration, lifespan events
│   │   ├── config.py                  # pydantic-settings Settings class, reads .env
│   │   ├── deps.py                    # Dependency injection: DB session, Redis, Qdrant client
│   │   │
│   │   ├── models/                    # Pydantic v2 models — single source of truth
│   │   │   ├── __init__.py
│   │   │   ├── incident.py            # IncidentReport, HazardEntity, SeverityTier enum
│   │   │   ├── retrieval.py           # SimilarIncident, RegulatoryClause
│   │   │   ├── risk.py                # RiskScore, RiskComponent, PrecursorPattern
│   │   │   └── output.py              # Alert, CorrAction, AnalysisReport, StreamUpdate
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── state.py               # SentinelState TypedDict definition
│   │   │   ├── graph.py               # LangGraph graph builder, conditional edges, compile()
│   │   │   └── nodes/
│   │   │       ├── __init__.py
│   │   │       ├── document_router.py # Classifies doc type, routes to correct path
│   │   │       ├── incident_parser.py # LLM extracts structured IncidentReport
│   │   │       ├── entity_extractor.py# spaCy NER + LLM verification pass
│   │   │       ├── pattern_detector.py# hybrid_search → precursor pattern matching
│   │   │       ├── regulatory_auditor.py # filtered RAG on Index B, violation detection
│   │   │       ├── risk_scorer.py     # calls compute_risk_score tool (pure Python)
│   │   │       ├── alert_synthesizer.py     # standard path (score < 8)
│   │   │       ├── priority_alert_synthesizer.py # critical path (score >= 8)
│   │   │       └── error_handler.py   # graceful degradation, partial result output
│   │   │
│   │   ├── tools/                     # @tool decorated pure functions, real Python logic
│   │   │   ├── __init__.py
│   │   │   ├── parsing.py             # parse_incident_report, extract_hazard_entities
│   │   │   ├── retrieval.py           # hybrid_search_incidents, retrieve_regulatory_clauses
│   │   │   ├── scoring.py             # compute_risk_score (the algorithm), classify_severity
│   │   │   ├── patterns.py            # detect_precursor_patterns, build_causal_chain
│   │   │   ├── actions.py             # generate_corrective_actions
│   │   │   └── streaming.py           # emit_stream_update (SSE queue helper)
│   │   │
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── chunker.py             # Semantic chunking: sentence-transformers similarity splits
│   │   │   ├── embedder.py            # bge-small-en-v1.5 singleton wrapper
│   │   │   ├── vector_store.py        # Qdrant client, 3-collection management, upsert
│   │   │   ├── bm25_index.py          # rank-bm25 index: build, serialize to disk, search
│   │   │   ├── retriever.py           # BM25 + Qdrant parallel → RRF → FlashRank → compress
│   │   │   └── compressor.py          # Contextual compression: strip off-topic sentences
│   │   │
│   │   ├── ingest/
│   │   │   ├── __init__.py
│   │   │   ├── loader.py              # pdfplumber primary → unstructured OCR fallback
│   │   │   ├── classifier.py          # LLM: classify as "incident" | "regulatory" | "unknown"
│   │   │   └── preprocessor.py        # Text clean: remove headers/footers, normalize whitespace
│   │   │
│   │   ├── knowledge_graph/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py               # NetworkX: add_incident, add_edges, find_precursor_chain
│   │   │   └── serializer.py          # JSON serialize/deserialize → Supabase (persist across restarts)
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py             # Supabase client + SQLAlchemy async session
│   │   │   ├── models.py              # SQLAlchemy ORM: Analysis, Alert tables
│   │   │   └── crud.py                # save_analysis, get_analysis, list_analyses (paginated)
│   │   │
│   │   ├── cache/
│   │   │   ├── __init__.py
│   │   │   └── client.py              # Upstash Redis: get_cached(sha256), set_cached, invalidate
│   │   │
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── analyze.py             # POST /analyze, GET /analyze/{id}/stream
│   │       ├── history.py             # GET /history, GET /history/{id}
│   │       └── health.py              # GET /health (UptimeRobot keep-alive target)
│   │
│   ├── scripts/
│   │   ├── ingest_corpus.py           # One-time: loads 80 PDFs from data/incidents/ into Qdrant Index A
│   │   └── seed_regulatory.py         # One-time: loads regulatory docs into Qdrant Index B
│   │
│   ├── data/
│   │   ├── incidents/                 # 80 OSHA/CSB/NIOSH PDFs (committed to repo or stored in S3)
│   │   └── regulatory/                # Indian Factories Act, OSHA 29CFR, EPA docs (text files)
│   │
│   ├── tests/
│   │   ├── test_tools.py              # Unit tests for all 10 tools
│   │   ├── test_rag.py                # Tests for chunker, retriever, RRF, FlashRank
│   │   ├── test_agents.py             # Integration tests for full LangGraph run
│   │   └── test_api.py                # FastAPI TestClient endpoint tests
│   │
│   ├── requirements.txt
│   ├── .env.example
│   └── render.yaml
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                 # Root layout, font vars, QueryClientProvider, Toaster
│   │   ├── page.tsx                   # Redirect to /dashboard
│   │   └── (dashboard)/
│   │       ├── layout.tsx             # Sidebar + TopNav shell
│   │       ├── page.tsx               # Dashboard: stats + recent alerts + charts
│   │       ├── analyze/
│   │       │   └── page.tsx           # Upload zone → live analysis → results
│   │       ├── incidents/
│   │       │   ├── page.tsx           # Incident explorer: filterable cards + table
│   │       │   └── [id]/
│   │       │       └── page.tsx       # Single incident: full report view
│   │       └── alerts/
│   │           └── page.tsx           # Alert center: all alerts, filter by severity
│   │
│   ├── components/
│   │   ├── ui/                        # shadcn/ui auto-generated (do not hand-edit)
│   │   ├── aceternity/                # Copied from ui.aceternity.com
│   │   │   ├── background-beams.tsx
│   │   │   ├── spotlight.tsx
│   │   │   ├── hover-border-gradient.tsx
│   │   │   ├── background-gradient.tsx
│   │   │   ├── text-generate-effect.tsx
│   │   │   └── meteors.tsx
│   │   ├── magicui/                   # Copied from magicui.design
│   │   │   ├── number-ticker.tsx
│   │   │   ├── shimmer-button.tsx
│   │   │   ├── border-beam.tsx
│   │   │   └── animated-shiny-text.tsx
│   │   │
│   │   ├── charts/
│   │   │   ├── RiskGauge.tsx          # SVG semicircle + framer-motion spring needle
│   │   │   ├── SeverityBarChart.tsx   # Recharts BarChart: analyses by severity
│   │   │   ├── IndustryHeatmap.tsx    # Recharts Treemap: industry × severity
│   │   │   └── TimelineChart.tsx      # Recharts LineChart: incidents over time
│   │   │
│   │   ├── analysis/
│   │   │   ├── UploadZone.tsx         # react-dropzone + BackgroundBeams + sample CTA
│   │   │   ├── PipelineVisual.tsx     # 7 agent nodes with SSE-driven state transitions
│   │   │   ├── RiskCard.tsx           # RiskGauge + score + severity badge + BackgroundGradient
│   │   │   ├── RegClauseCard.tsx      # Collapsible: clause text + source + confidence
│   │   │   ├── PrecursorList.tsx      # Detected patterns + historical evidence count
│   │   │   ├── CausalChainView.tsx    # Vertical timeline of causal events
│   │   │   └── ActionList.tsx         # Corrective actions grouped by urgency tier
│   │   │
│   │   ├── dashboard/
│   │   │   ├── StatCard.tsx           # NumberTicker metric + trend indicator
│   │   │   ├── RecentAlerts.tsx       # Last 10 alerts feed
│   │   │   └── RiskHeatmap.tsx        # Industry × severity grid (color-coded cells)
│   │   │
│   │   └── layout/
│   │       ├── Sidebar.tsx            # Desktop nav sidebar with icons + labels
│   │       ├── TopNav.tsx             # Top bar: breadcrumb + actions
│   │       └── MobileNav.tsx          # Sheet-based bottom-up mobile nav
│   │
│   ├── lib/
│   │   ├── api.ts                     # Fetch wrappers + SSE EventSource client
│   │   ├── types.ts                   # TypeScript interfaces mirroring backend Pydantic models
│   │   ├── utils.ts                   # cn() utility (clsx + tailwind-merge)
│   │   └── constants.ts               # SEVERITY_CONFIG, AGENT_STAGES, INDUSTRY_LABELS
│   │
│   ├── hooks/
│   │   ├── useSSE.ts                  # EventSource hook with cleanup + error handling
│   │   ├── useAnalysis.ts             # Upload mutation + SSE subscription + state machine
│   │   └── useAnimatedNumber.ts       # requestAnimationFrame counter (0 → target in 1200ms)
│   │
│   ├── store/
│   │   └── sentinel.ts                # Zustand: currentAnalysis, analysisHistory, globalAlerts
│   │
│   ├── styles/
│   │   └── globals.css                # CSS variables + Tailwind @layer base styles
│   │
│   ├── public/
│   │   └── sample-report.pdf          # Pre-bundled OSHA incident PDF for "Try a sample" CTA
│   │
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   └── tsconfig.json
│
├── .github/
│   └── workflows/
│       ├── deploy-backend.yml         # Auto-deploy to Render on push to main/backend/**
│       └── deploy-frontend.yml        # Auto-deploy to Vercel on push to main/frontend/**
│
└── PRD.md
```

---

## 6. Environment Variables

**`backend/.env`** (never commit this file):
```env
# LLM APIs
GEMINI_API_KEY=your_key_here          # Get at: aistudio.google.com → "Get API key"
GROQ_API_KEY=your_key_here            # Get at: console.groq.com → API Keys

# Vector Store
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_key_here          # Get at: cloud.qdrant.io

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here       # Project Settings → API → anon public
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/postgres

# Cache
UPSTASH_REDIS_REST_URL=https://your.upstash.io
UPSTASH_REDIS_REST_TOKEN=your_token_here  # Get at: console.upstash.com

# App
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,https://your-app.vercel.app
MAX_ANALYSES_PER_IP_PER_HOUR=10
ANALYSIS_CACHE_TTL_SECONDS=3600

# Qdrant collection names
INCIDENTS_COLLECTION=sentinel_incidents
REGULATORY_COLLECTION=sentinel_regulatory
ACTIONS_COLLECTION=sentinel_actions
```

**`frontend/.env.local`** (never commit):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**`frontend/.env.production`** (set via Vercel dashboard, not committed):
```env
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
```

**`backend/.env.example`** (commit this with placeholder values):
Copy from above, replace all values with `your_key_here`.

**`backend/app/config.py`:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gemini_api_key: str
    groq_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    supabase_url: str
    supabase_key: str
    database_url: str
    upstash_redis_rest_url: str
    upstash_redis_rest_token: str
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"
    max_analyses_per_ip_per_hour: int = 10
    analysis_cache_ttl_seconds: int = 3600
    incidents_collection: str = "sentinel_incidents"
    regulatory_collection: str = "sentinel_regulatory"
    actions_collection: str = "sentinel_actions"

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 7. Data Corpus Setup

### Real Free Data Sources

| Source | Document Type | Count | URL |
|---|---|---|---|
| OSHA IMIS Accident Investigation | Incident reports | 40 PDFs | osha.gov/pls/imis/AccidentSearch |
| CSB (Chemical Safety Board) | Investigation reports | 15 PDFs | csb.gov/investigations |
| NIOSH FACE Program | Fatality case studies | 15 PDFs | cdc.gov/niosh/face |
| UK HSE | Investigation reports | 10 PDFs | hse.gov.uk/comah/sragtech |
| Indian Factories Act 1948 | Regulatory text | 1 doc | legislation.gov.in |
| OSHA 29 CFR 1910 (General Industry) | Regulatory standards | 1 doc | osha.gov/laws-regs/regulations/standardnumber/1910 |
| OSHA 29 CFR 1926 (Construction) | Regulatory standards | 1 doc | osha.gov/laws-regs/regulations/standardnumber/1926 |
| EPA Risk Management Program | Regulatory | 1 doc | epa.gov/rmp |

**Target: 80 incident PDFs + 5 regulatory documents**

All are publicly available at no cost. Download and commit to `backend/data/`.

### One-Time Ingestion (run before deployment)

```bash
# From backend/ directory with venv active and .env loaded
python scripts/ingest_corpus.py    # loads all PDFs into Qdrant Index A + builds BM25 index
python scripts/seed_regulatory.py  # loads regulatory docs into Qdrant Index B
```

**`scripts/ingest_corpus.py` does:**
1. Load all PDFs from `data/incidents/` using pdfplumber
2. Clean text via `ingest/preprocessor.py`
3. Semantic chunk using `rag/chunker.py`
4. Generate bge-small-en-v1.5 embeddings via `rag/embedder.py`
5. Upsert chunks to Qdrant `sentinel_incidents` collection
6. Build BM25 index via `rag/bm25_index.py` → serialize to `data/bm25_incidents.pkl`
7. Build NetworkX KG skeleton → serialize to Supabase via `knowledge_graph/serializer.py`

**This script runs once locally.** Qdrant Cloud collection persists. On Render, the app just connects to the same cloud collection — no re-ingestion needed.

---

## 8. Backend Implementation

### 8.1 Pydantic Models (source of truth for the entire system)

**`app/models/incident.py`:**
```python
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List

class SeverityTier(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class HazardEntity(BaseModel):
    text: str
    entity_type: str  # HAZARD | EQUIPMENT | CHEMICAL | CONDITION | UNSAFE_ACT
    confidence: float = Field(ge=0.0, le=1.0)
    source: str  # "spacy" | "llm"

class IncidentReport(BaseModel):
    incident_date: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    equipment_involved: List[str] = []
    sequence_of_events: str = ""
    immediate_causes: List[str] = []
    root_causes: List[str] = []
    injury_count: int = 0
    fatality_count: int = 0
    severity_indicator: str = "UNKNOWN"
    raw_text_length: int = 0
    extraction_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
```

**`app/models/retrieval.py`:**
```python
class SimilarIncident(BaseModel):
    doc_id: str
    title: str
    industry: str
    severity: str
    similarity_score: float
    chunk_excerpt: str
    source_document: str
    incident_date: Optional[str] = None

class RegulatoryClause(BaseModel):
    clause_id: str
    regulation_name: str  # e.g. "OSHA 29 CFR 1910.147"
    section: str
    clause_text: str
    violation_confidence: float = Field(ge=0.0, le=1.0)
    relevance_explanation: str
```

**`app/models/risk.py`:**
```python
class RiskComponent(BaseModel):
    name: str          # "Severity" | "Frequency" | "Regulatory" | "Precursor Density"
    score: float = Field(ge=0.0, le=10.0)
    weight: float
    explanation: str

class PrecursorPattern(BaseModel):
    pattern_name: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_count: int  # number of historical incidents with this pattern
    hazard_types: List[str] = []

class RiskScore(BaseModel):
    total: float = Field(ge=0.0, le=10.0)
    tier: SeverityTier
    components: List[RiskComponent]
    explanation: str
```

**`app/models/output.py`:**
```python
import uuid
from datetime import datetime

class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    severity: SeverityTier
    title: str
    description: str
    regulatory_violations: List[str] = []
    precursor_patterns: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class CorrAction(BaseModel):
    urgency: str  # "IMMEDIATE" | "SHORT_TERM" | "LONG_TERM"
    action: str
    rationale: str
    regulation_reference: Optional[str] = None

class AnalysisReport(BaseModel):
    analysis_id: str
    file_name: str
    incident: IncidentReport
    entities: List[HazardEntity]
    similar_incidents: List[SimilarIncident]
    regulatory_clauses: List[RegulatoryClause]
    precursor_patterns: List[PrecursorPattern]
    risk_score: RiskScore
    alerts: List[Alert]
    corrective_actions: List[CorrAction]
    processing_time_seconds: float
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class StreamUpdate(BaseModel):
    stage: str          # agent node name
    status: str         # "started" | "completed" | "error"
    message: str        # human-readable, shown in PipelineVisual
    data: Optional[dict] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
```

---

### 8.2 LangGraph State Machine

**`app/agents/state.py`:**
```python
from typing import TypedDict, Optional, List, Literal
import asyncio

class SentinelState(TypedDict):
    raw_text: str
    file_name: str
    document_type: Literal["incident", "regulatory", "unknown"]
    incident: Optional[dict]
    entities: List[dict]
    similar_incidents: List[dict]
    regulatory_clauses: List[dict]
    precursor_patterns: List[dict]
    risk_score: Optional[dict]
    alerts: List[dict]
    corrective_actions: List[dict]
    analysis_report: Optional[dict]
    error: Optional[str]
    processing_stage: str
    iteration_count: int
    analysis_id: str
    stream_queue: Optional[asyncio.Queue]  # SSE event queue
```

**`app/agents/graph.py`:**
```python
from langgraph.graph import StateGraph, END
from .state import SentinelState
from .nodes import (
    document_router, incident_parser, entity_extractor,
    pattern_detector, regulatory_auditor, risk_scorer,
    alert_synthesizer, priority_alert_synthesizer, error_handler
)

def route_by_risk(state: SentinelState) -> str:
    score = (state.get("risk_score") or {}).get("total", 0)
    return "priority" if score >= 8.0 else "standard"

def build_graph() -> StateGraph:
    g = StateGraph(SentinelState)
    g.add_node("document_router", document_router)
    g.add_node("incident_parser", incident_parser)
    g.add_node("entity_extractor", entity_extractor)
    g.add_node("pattern_detector", pattern_detector)
    g.add_node("regulatory_auditor", regulatory_auditor)
    g.add_node("risk_scorer", risk_scorer)
    g.add_node("alert_synthesizer", alert_synthesizer)
    g.add_node("priority_alert_synthesizer", priority_alert_synthesizer)
    g.add_node("error_handler", error_handler)

    g.set_entry_point("document_router")
    g.add_edge("document_router", "incident_parser")
    g.add_edge("incident_parser", "entity_extractor")
    g.add_edge("entity_extractor", "pattern_detector")
    g.add_edge("pattern_detector", "regulatory_auditor")
    g.add_edge("regulatory_auditor", "risk_scorer")
    g.add_conditional_edges(
        "risk_scorer",
        route_by_risk,
        {"priority": "priority_alert_synthesizer", "standard": "alert_synthesizer"}
    )
    g.add_edge("alert_synthesizer", END)
    g.add_edge("priority_alert_synthesizer", END)
    return g.compile()

SENTINEL_GRAPH = build_graph()
```

**Node template (`app/agents/nodes/incident_parser.py`):**
```python
from ..state import SentinelState
from app.tools.parsing import parse_incident_report
from app.models.output import StreamUpdate

async def incident_parser(state: SentinelState) -> SentinelState:
    await _emit(state, "incident_parser", "started", "Extracting incident structure...")
    try:
        result = await parse_incident_report(state["raw_text"])
        await _emit(state, "incident_parser", "completed",
                    f"Parsed: {result.industry or 'Unknown industry'}, severity: {result.severity_indicator}")
        return {**state, "incident": result.model_dump(), "processing_stage": "entity_extractor"}
    except Exception as e:
        return {**state, "error": str(e), "processing_stage": "error_handler"}

async def _emit(state, stage, status, message):
    if queue := state.get("stream_queue"):
        await queue.put(StreamUpdate(stage=stage, status=status, message=message))
```

---

### 8.3 Tool Registry

**Tool 1 — `parse_incident_report`:**
LLM extraction with Gemini 2.0 Flash + Pydantic output parser. System prompt instructs strict JSON output matching IncidentReport schema. If LLM output fails schema validation, retry once with corrected prompt. No guessing from thin air.

**Tool 2 — `extract_hazard_entities`:**
spaCy `en_core_web_lg` NER first pass. Custom entity ruler adds HAZARD / EQUIPMENT / CHEMICAL / CONDITION / UNSAFE_ACT labels. LLM verification pass only for entities with spaCy confidence < 0.7. Result: `List[HazardEntity]` with source tagged.

**Tool 3 — `hybrid_search_incidents`:**
```python
@tool
def hybrid_search_incidents(query: str, industry: str = None, k: int = 8) -> List[dict]:
    """Search historical incidents using BM25 + dense vectors + RRF + FlashRank reranking."""
    filters = {"industry": industry} if industry else {}

    # Run BM25 and Qdrant dense in parallel
    bm25_hits = bm25_index.get_top_n(query.split(), corpus, n=20)
    dense_hits = qdrant.search("sentinel_incidents", embedder.encode(query),
                               query_filter=filters, limit=20)

    # RRF merge: score = sum(1/(rank + 60)) for each doc across both lists
    merged = reciprocal_rank_fusion([bm25_hits, dense_hits])

    # FlashRank cross-encoder rerank
    reranked = flashrank.rerank(query, merged[:20], top_n=k)

    # Contextual compression: trim sentences below 0.3 cosine similarity to query
    return compress_results(reranked)
```

**Tool 4 — `retrieve_regulatory_clauses`:**
Filtered RAG on Qdrant `sentinel_regulatory` collection. Filter: `hazard_type` + `industry` metadata. Same hybrid search + FlashRank pipeline. Returns `List[RegulatoryClause]` with source citation.

**Tool 5 — `compute_risk_score` (pure Python, no LLM):**
```python
CLAUSE_WEIGHT_MAP = {
    "general_duty_clause": 2.0,
    "lockout_tagout": 1.8,
    "confined_space": 1.9,
    "machine_guarding": 1.7,
    "fall_protection": 1.6,
    "ppe_required": 1.5,
    "hazcom": 1.4,
    "housekeeping": 1.0,
}

SEVERITY_TO_SCORE = {"CRITICAL": 9.5, "HIGH": 7.5, "MEDIUM": 5.0, "LOW": 2.5, "UNKNOWN": 4.0}

@tool
def compute_risk_score(severity_indicator, similar_count, corpus_size,
                       violated_clauses, detected_precursors, known_precursors) -> dict:
    """Pure Python multi-dimensional risk scoring. No LLM."""
    s = SEVERITY_TO_SCORE.get(severity_indicator, 4.0)
    f = min((similar_count / max(corpus_size, 1)) * 100, 10.0)
    r = min(sum(CLAUSE_WEIGHT_MAP.get(c, 1.0) for c in violated_clauses) * 1.2, 10.0)
    p = min((detected_precursors / max(known_precursors, 1)) * 10.0, 10.0)
    total = round(0.30*s + 0.25*f + 0.25*r + 0.20*p, 2)
    tier = "CRITICAL" if total >= 8 else "HIGH" if total >= 6 else "MEDIUM" if total >= 4 else "LOW"
    return {
        "total": total, "tier": tier,
        "components": [
            {"name": "Severity", "score": s, "weight": 0.30, "explanation": f"Severity tier: {severity_indicator}"},
            {"name": "Frequency", "score": f, "weight": 0.25, "explanation": f"{similar_count} similar incidents found"},
            {"name": "Regulatory", "score": r, "weight": 0.25, "explanation": f"{len(violated_clauses)} clause violations"},
            {"name": "Precursor Density", "score": p, "weight": 0.20, "explanation": f"{detected_precursors}/{known_precursors} precursors detected"},
        ]
    }
```

**Tool 6 — `detect_precursor_patterns`:**
Compare current incident entity set against entity sets of historically retrieved similar incidents. Flag patterns that appear in 3+ historical incidents. Return `List[PrecursorPattern]` with evidence_count for credibility.

**Tool 7 — `build_causal_chain`:**
Traverse NetworkX graph from the incident node. Follow `CAUSED_BY` and `PRECEDED_BY` edges. Return ordered event list for frontend timeline visualization.

**Tool 8 — `classify_severity`:**
Rule-based first pass: keyword detection for fatality/hospitalization/near-miss. Returns CRITICAL/HIGH/MEDIUM/LOW. LLM refinement only for ambiguous cases where no keywords match. No unnecessary API call on clear-cut cases.

**Tool 9 — `generate_corrective_actions`:**
Lookup table: hazard_type → action templates (stored as JSON in `data/actions.json`). LLM synthesis only for hazard types not in lookup. Output sorted by urgency: IMMEDIATE first, then SHORT_TERM, then LONG_TERM.

**Tool 10 — `emit_stream_update`:**
Helper that puts a `StreamUpdate` into the `asyncio.Queue` in state. The API route reads from this queue and yields SSE events. Keeps streaming logic out of tool implementations.

---

### 8.4 Hybrid Retrieval — Implementation Detail

**`app/rag/retriever.py`:**
```python
def reciprocal_rank_fusion(result_lists: List[List[dict]], k: int = 60) -> List[dict]:
    """
    RRF: score(doc) = sum over lists of (1 / (rank_in_list + k))
    k=60 is the standard parameter from the original RRF paper.
    Higher k reduces the impact of top-ranked documents.
    """
    scores = {}
    for result_list in result_lists:
        for rank, doc in enumerate(result_list):
            doc_id = doc["id"]
            scores[doc_id] = scores.get(doc_id, 0) + (1 / (rank + k))
    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_map[doc_id] for doc_id, _ in sorted_docs]
```

**`app/rag/chunker.py` — semantic chunking logic:**
```python
# Uses sentence-transformers to compute cosine similarity between adjacent sentences.
# When similarity drops below threshold (0.5), create a new chunk boundary.
# Each chunk stores: text, parent_section, doc_id, metadata
# Typical result: 200-600 token chunks that respect semantic boundaries.
# Also stores parent section reference for the parent document retriever pattern:
# retrieve small chunks, return parent section to LLM for full context.
```

---

### 8.5 API Routes + SSE Streaming

**`app/api/analyze.py`:**
```python
@router.post("/analyze")
async def start_analysis(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    request: Request = None,
    db = Depends(get_db),
    redis = Depends(get_redis)
):
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    content = await file.read()
    if len(content) < 100:
        raise HTTPException(400, "File appears to be empty or corrupt")

    # Redis cache: check SHA256 hash
    file_hash = hashlib.sha256(content).hexdigest()
    cached_id = await redis.get(f"cache:{file_hash}")
    if cached_id:
        return {"analysis_id": cached_id, "status": "cached"}

    # Create analysis record in Supabase
    analysis_id = str(uuid.uuid4())
    await crud.create_analysis(db, analysis_id, file.filename)

    # Store file temporarily
    temp_path = f"/tmp/{analysis_id}.pdf"
    with open(temp_path, "wb") as f:
        f.write(content)

    # Run analysis in background
    background_tasks.add_task(run_analysis, analysis_id, temp_path, file.filename, file_hash)

    return {"analysis_id": analysis_id, "status": "processing"}


@router.get("/analyze/{analysis_id}/stream")
async def stream_analysis(analysis_id: str):
    queue = asyncio.Queue()
    stream_queues[analysis_id] = queue  # global dict, keyed by analysis_id

    async def event_generator():
        while True:
            try:
                update: StreamUpdate = await asyncio.wait_for(queue.get(), timeout=60.0)
                yield f"data: {update.model_dump_json()}\n\n"
                if update.stage == "complete" or update.stage == "error":
                    break
            except asyncio.TimeoutError:
                yield "data: {\"stage\":\"heartbeat\",\"status\":\"alive\",\"message\":\"\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )
```

**IP rate limiting middleware (add to `app/main.py`):**
```python
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path == "/analyze" and request.method == "POST":
        ip = request.client.host
        key = f"rl:{ip}"
        count = int(await redis_client.incr(key) or 0)
        if count == 1:
            await redis_client.expire(key, 3600)
        if count > settings.max_analyses_per_ip_per_hour:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Try again later."})
    return await call_next(request)
```

---

## 9. Frontend Implementation

### 9.1 Design System

**`styles/globals.css`:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* Background layers */
    --bg-base: #080810;
    --bg-surface: #0F0F1A;
    --bg-card: #16162A;
    --bg-card-hover: #1C1C34;

    /* Borders */
    --border-subtle: #1E1E32;
    --border-default: #2A2A42;
    --border-strong: #3A3A5A;

    /* Severity */
    --severity-critical: #FF3B30;
    --severity-critical-bg: rgba(255, 59, 48, 0.12);
    --severity-critical-border: rgba(255, 59, 48, 0.25);
    --severity-high: #FF6B00;
    --severity-high-bg: rgba(255, 107, 0, 0.12);
    --severity-high-border: rgba(255, 107, 0, 0.25);
    --severity-medium: #FFB800;
    --severity-medium-bg: rgba(255, 184, 0, 0.12);
    --severity-medium-border: rgba(255, 184, 0, 0.25);
    --severity-low: #30D158;
    --severity-low-bg: rgba(48, 209, 88, 0.12);
    --severity-low-border: rgba(48, 209, 88, 0.25);

    /* Accent */
    --accent: #4F8EF7;
    --accent-hover: #6BA3F9;
    --accent-glow: rgba(79, 142, 247, 0.20);

    /* Text */
    --text-primary: #F0F0FA;
    --text-secondary: #8888AA;
    --text-muted: #5A5A7A;

    /* Pipeline node states */
    --stage-idle: #2A2A42;
    --stage-active: #4F8EF7;
    --stage-complete: #30D158;
    --stage-error: #FF3B30;

    /* Fonts */
    --font-display: 'Bricolage Grotesque', sans-serif;
    --font-body: 'DM Sans', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
  }

  html { background-color: var(--bg-base); }
  body {
    font-family: var(--font-body);
    color: var(--text-primary);
    background-color: var(--bg-base);
    -webkit-font-smoothing: antialiased;
  }
}
```

**`tailwind.config.ts` additions:**
```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          base: 'var(--bg-base)',
          surface: 'var(--bg-surface)',
          card: 'var(--bg-card)',
        },
        severity: {
          critical: 'var(--severity-critical)',
          high: 'var(--severity-high)',
          medium: 'var(--severity-medium)',
          low: 'var(--severity-low)',
        },
        accent: 'var(--accent)',
        border: {
          subtle: 'var(--border-subtle)',
          default: 'var(--border-default)',
          strong: 'var(--border-strong)',
        },
        text: {
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          muted: 'var(--text-muted)',
        },
      },
      fontFamily: {
        display: ['var(--font-display)'],
        body: ['var(--font-body)'],
        mono: ['var(--font-mono)'],
      },
      animation: {
        'pulse-critical': 'pulse-critical 2s ease-in-out infinite',
        'border-beam': 'border-beam 4s linear infinite',
      },
      keyframes: {
        'pulse-critical': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(255, 59, 48, 0)' },
          '50%': { boxShadow: '0 0 0 8px rgba(255, 59, 48, 0.2)' },
        },
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}
export default config
```

**`lib/constants.ts`:**
```typescript
export const SEVERITY_CONFIG = {
  CRITICAL: {
    label: 'Critical',
    color: 'var(--severity-critical)',
    bg: 'var(--severity-critical-bg)',
    border: 'var(--severity-critical-border)',
    tailwind: 'text-red-400 bg-red-500/10 border-red-500/20',
    pulse: true,
    gaugeColor: '#FF3B30',
  },
  HIGH: {
    label: 'High',
    color: 'var(--severity-high)',
    bg: 'var(--severity-high-bg)',
    border: 'var(--severity-high-border)',
    tailwind: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
    pulse: false,
    gaugeColor: '#FF6B00',
  },
  MEDIUM: {
    label: 'Medium',
    color: 'var(--severity-medium)',
    bg: 'var(--severity-medium-bg)',
    border: 'var(--severity-medium-border)',
    tailwind: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
    pulse: false,
    gaugeColor: '#FFB800',
  },
  LOW: {
    label: 'Low',
    color: 'var(--severity-low)',
    bg: 'var(--severity-low-bg)',
    border: 'var(--severity-low-border)',
    tailwind: 'text-green-400 bg-green-500/10 border-green-500/20',
    pulse: false,
    gaugeColor: '#30D158',
  },
} as const

export const AGENT_STAGES = [
  { id: 'document_router',     label: 'Router',     icon: 'Compass' },
  { id: 'incident_parser',     label: 'Parser',     icon: 'FileText' },
  { id: 'entity_extractor',    label: 'Extractor',  icon: 'Tag' },
  { id: 'pattern_detector',    label: 'Patterns',   icon: 'Activity' },
  { id: 'regulatory_auditor',  label: 'Auditor',    icon: 'Scale' },
  { id: 'risk_scorer',         label: 'Scorer',     icon: 'BarChart2' },
  { id: 'alert_synthesizer',   label: 'Alerts',     icon: 'Bell' },
] as const
```

---

### 9.2 Typography

**`app/layout.tsx`:**
```typescript
import { Bricolage_Grotesque, DM_Sans, JetBrains_Mono } from 'next/font/google'

const bricolage = Bricolage_Grotesque({
  subsets: ['latin'],
  variable: '--font-display',
  weight: ['400', '500', '600', '700', '800'],
  display: 'swap',
})

const dmSans = DM_Sans({
  subsets: ['latin'],
  variable: '--font-body',
  weight: ['400', '500', '600'],
  display: 'swap',
})

const jetbrains = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  weight: ['400', '500'],
  display: 'swap',
})

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${bricolage.variable} ${dmSans.variable} ${jetbrains.variable}`}>
      <body>{children}</body>
    </html>
  )
}
```

**Typography usage rules:**
- `font-display font-bold` — all headings (H1-H3), risk score number, stat card numbers
- `font-body` — body text, labels, descriptions (set as body default, no class needed)
- `font-mono` — risk score component values, regulatory citations, analysis IDs, code
- Never use: Inter, Roboto, Arial, system-ui as display or heading fonts
- Risk score: `font-display text-7xl font-extrabold` — the centerpiece number
- Section headings: `font-display text-2xl font-bold`
- Card titles: `font-display text-lg font-semibold`

---

### 9.3 Key Component Specs

**`components/charts/RiskGauge.tsx`:**
```
SVG semicircle gauge:
- ViewBox: "0 0 240 140"
- Arc path: 180° from left to right (9 o'clock to 3 o'clock)
- Segment colors:
    0°-54°  (0-3 score): #30D158 (LOW / green)
    54°-108° (3-6 score): #FFB800 (MEDIUM / yellow)
    108°-144° (6-8 score): #FF6B00 (HIGH / orange)
    144°-180° (8-10 score): #FF3B30 (CRITICAL / red)
- Needle: thin line from center, rotates to (score/10)*180°
- Animation: useMotionValue(0) → useSpring → animate to target angle on mount
  Spring config: { stiffness: 60, damping: 15 } (slow, satisfying settle)
- Score text: center of arc, font-display font-extrabold text-5xl
- Tier label: below score, font-body text-sm, colored per SEVERITY_CONFIG
- Outer ring: subtle box-shadow glow in severity color
- CRITICAL: add pulse-critical animation to outer ring
```

**`components/analysis/PipelineVisual.tsx`:**
```
Horizontal row of 7 circular nodes from AGENT_STAGES constant.
Between each node: a thin horizontal connecting line.

Per node state:
  idle:     bg-stage-idle, border-border-subtle, muted icon
  active:   bg-accent/10, border-accent, accent icon, pulse animation
  complete: bg-green-500/10, border-green-500/30, green checkmark icon
  error:    bg-red-500/10, border-red-500/30, red X icon

SSE-driven: useSSE hook updates node states in order as events arrive.
Active node shows agent label + status message below the row.
framer-motion AnimatePresence for state transitions (duration 0.3s).

Mobile: collapse to vertical stepper layout below md breakpoint.
```

**`components/analysis/UploadZone.tsx`:**
```
Full-width drop zone, minimum height 320px.
react-dropzone: accept PDF only, maxSize 10MB.
Aceternity BackgroundBeams as absolute-positioned background.
Dashed border, 2px, border-border-default.
On hover: border-accent, bg-accent/5 transition.
On drag-over: border-accent, scale(1.01), bg-accent/10.

Content:
  - Upload icon (lucide CloudUpload, 48px, text-secondary)
  - "Drop your incident report here" (font-display text-xl)
  - "PDF files up to 10MB" (text-secondary text-sm)
  - "or click to browse" (text-accent underline, cursor-pointer)
  - Divider "—or—"
  - "Try a sample OSHA report" link (ShimmerButton, small)

After file selected:
  - File name + size badge
  - "Run Analysis" button (HoverBorderGradient wrapper, full width)
  - "Remove" text link

Error state: border-red-500/30, red error message, "Try again" link.
```

**`components/analysis/RegClauseCard.tsx`:**
```
shadcn Collapsible component.
Header (always visible):
  - Regulation name (font-mono text-sm, text-accent)
  - Section (text-muted text-xs)
  - Violation confidence badge (severity color matching confidence level)
  - Chevron icon rotating on expand
  - HoverBorderGradient wrapper (border color = violation severity)

Expanded content:
  - Clause text in font-mono text-xs, text-secondary, bg-bg-surface rounded p-3
  - "Source:" label + document name + page reference
  - "Relevance:" explanation in font-body text-sm
```

**`components/dashboard/StatCard.tsx`:**
```
Card with bg-bg-card, border-border-subtle, rounded-xl, p-6.
Top: metric label (text-secondary text-sm uppercase tracking-wider)
Center: NumberTicker (Magic UI) — animated from 0 to value on mount
        font-display font-bold text-4xl text-primary
Bottom: trend indicator — green ↑ or red ↓ with delta percentage
        (only if trend data available, else omit)
Subtle radial gradient behind the number in accent color at 5% opacity.
```

---

### 9.4 Page Architecture

**`/analyze` page flow:**

```
Phase 1 — Upload (initial state):
  Full viewport height. BackgroundBeams behind the zone.
  UploadZone centered. No sidebar content highlighted.

Phase 2 — Processing (after "Run Analysis"):
  File info bar at top: filename + size chip.
  PipelineVisual below: 7 nodes, SSE-driven live updates.
  Below pipeline: 4 skeleton loading cards (one per incoming section).
  Agent status message animates in below active node.

Phase 3 — Complete (all SSE sections received):
  TextGenerateEffect: "Analysis Complete" heading appears.
  Sections reveal with staggered framer-motion (0.08s delay each):
    1. RiskCard (gauge + score + severity) — most prominent, full width top
    2. PrecursorList (detected patterns + evidence) — left col
    3. RegClauseCard list (regulatory violations) — right col
    4. CausalChainView (event timeline) — full width
    5. ActionList (corrective actions by tier) — full width bottom
  Action bar: "Download PDF Summary" (ShimmerButton) + "View in Incidents" link.
```

**`/dashboard` page:**
```
Top row: 4 StatCards — Total Analyses | Critical Alerts | Avg Risk Score | Industries Covered
Middle: SeverityBarChart (left, 60%) + RecentAlerts feed (right, 40%)
Bottom: IndustryHeatmap (full width, color-coded grid)
Background: Meteors (Aceternity, 12 meteors, opacity 0.3)
```

**`/incidents` page:**
```
Filter bar: severity tabs (All / CRITICAL / HIGH / MEDIUM / LOW) + industry dropdown + date range
Card grid: 3-col on desktop, 1-col on mobile
Each card: severity badge + industry + date + risk score + "View Report" CTA
Pagination: load more button (not infinite scroll — judges can count pages)
```

---

### 9.5 Animation Guidelines

**Page transitions (wrap all page content):**
```typescript
const pageVariants = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.4, 0, 0.2, 1] } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.2 } },
}
```

**Staggered card reveals:**
```typescript
const container = { animate: { transition: { staggerChildren: 0.08 } } }
const card = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] } },
}
```

**CRITICAL alert pulse (only CRITICAL, max 1 looping animation per page):**
```typescript
// On the outer wrapper of the RiskCard when severity is CRITICAL
animate={{
  boxShadow: [
    '0 0 0 0 rgba(255, 59, 48, 0)',
    '0 0 0 10px rgba(255, 59, 48, 0.18)',
    '0 0 0 0 rgba(255, 59, 48, 0)',
  ]
}}
transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
```

**Pipeline node active pulse:**
```typescript
animate={{
  scale: [1, 1.06, 1],
  boxShadow: [
    '0 0 0 0 var(--accent-glow)',
    '0 0 14px 4px var(--accent-glow)',
    '0 0 0 0 var(--accent-glow)'
  ]
}}
transition={{ duration: 1.4, repeat: Infinity, ease: 'easeInOut' }}
```

**Risk gauge needle spring:**
```typescript
const angle = useMotionValue(0)
const smoothAngle = useSpring(angle, { stiffness: 60, damping: 15 })
useEffect(() => { angle.set((riskScore / 10) * 180) }, [riskScore])
// Apply smoothAngle to SVG rotate transform on the needle element
```

**Rules (do not violate):**
- Max 1 looping animation visible at a time per viewport
- All non-loop animations are one-shot on mount
- No bounce easings — only `[0.4, 0, 0.2, 1]` (Material Design standard) or `easeInOut`
- Respect `prefers-reduced-motion`: wrap all animations with the Framer Motion `useReducedMotion()` check
- Duration range: 200ms–500ms for one-shot, 1400ms–2200ms for loops
- Never animate `width` or `height` — only `transform` and `opacity` for performance

---

### 9.6 Aceternity UI Usage Guide

All from **https://ui.aceternity.com/components** — MIT license, free, copy the `.tsx` file.

| Component | Location in app | Customization notes |
|---|---|---|
| `BackgroundBeams` | `/analyze` upload zone — `absolute inset-0 z-0` | Beam color: `var(--accent)`. Reduce beam count to 6. |
| `Spotlight` | CRITICAL `RiskCard` wrapper | Spotlight color: `var(--severity-critical)`. Radius 300. |
| `HoverBorderGradient` | Primary "Run Analysis" button wrapper | Gradient: `accent → cyan-400`. Duration 3s. |
| `BackgroundGradient` | `RiskCard` outer glow wrapper | Gradient colors: match severity tier color. Blur 20. |
| `TextGenerateEffect` | "Analysis Complete" heading reveal | Font: `font-display font-bold text-3xl`. Duration 0.6. |
| `Meteors` | `/dashboard` background, `absolute inset-0 z-0` | Count: 12. Reduce size. Opacity 0.3 wrapper div. |

**Install pattern for all Aceternity components:**
```bash
# 1. Copy the .tsx source from ui.aceternity.com
# 2. Place in components/aceternity/<component-name>.tsx
# 3. Ensure framer-motion and clsx are installed (already done)
# 4. Import directly: import { BackgroundBeams } from "@/components/aceternity/background-beams"
```

---

### 9.7 Magic UI Usage Guide

All from **https://magicui.design/docs** — MIT license, free, copy-paste.

| Component | Location in app | Customization notes |
|---|---|---|
| `NumberTicker` | `StatCard.tsx` metric, `RiskCard.tsx` score | Match `--font-display`. `decimalPlaces={1}` for risk score. |
| `ShimmerButton` | "Try a sample" CTA, "Download PDF" button | Background: `var(--bg-card)`. Shimmer: `var(--accent)`. |
| `BorderBeam` | `RiskCard` wrapper during SSE loading | `size={250}`, `duration={8}`. Color: `var(--accent)`. Speed up to `duration={4}` for CRITICAL. |
| `AnimatedShinyText` | CRITICAL severity badge text only | Shiny color: `var(--severity-critical)`. |

---

## 10. API Reference

```
POST   /analyze
  Body:     multipart/form-data { file: PDF, max 10MB }
  Response: { analysis_id: string, status: "processing" | "cached" }
  Rate:     10 requests/IP/hour (429 if exceeded)
  Cache:    SHA256 hash match → returns existing analysis_id instantly

GET    /analyze/{analysis_id}/stream
  Response: text/event-stream (SSE)
  Events:   StreamUpdate JSON per agent node + final AnalysisReport
  Heartbeat: every 30s to keep connection alive

GET    /analyze/{analysis_id}
  Response: Full AnalysisReport JSON (from Supabase)

GET    /history
  Query: page=1, limit=20, severity=CRITICAL, industry=construction
  Response: { items: AnalysisReport[], total: int, page: int }

GET    /history/{analysis_id}
  Response: Full AnalysisReport JSON

GET    /health
  Response: { status: "ok", version: "1.0.0", timestamp: "..." }
  Used by: UptimeRobot (ping every 14 minutes to prevent Render cold start)
```

**SSE event shape:**
```json
data: {
  "stage": "pattern_detector",
  "status": "completed",
  "message": "Found 4 precursor patterns across 9 historical incidents",
  "data": { "pattern_count": 4 },
  "timestamp": "2026-09-20T10:30:00Z"
}
```

**Final SSE event:**
```json
data: {
  "stage": "complete",
  "status": "completed",
  "message": "Analysis complete",
  "data": { /* full AnalysisReport object */ },
  "timestamp": "..."
}
```

---

## 11. Clean Code Rules

### Python (backend)

1. **Single responsibility.** `api/` routes contain zero business logic. They call agent functions and return responses. Logic lives in `agents/`, `tools/`, `rag/`.

2. **One model definition.** All Pydantic models defined once in `models/`. Never define inline dicts or anonymous schemas in routes or tools.

3. **Pure tools.** Every `@tool` function is side-effect free except for explicit I/O passed as parameters. No global state mutation inside tools.

4. **Full type hints.** Every function has typed parameters and return type. `-> dict` is never acceptable — use the actual model type.

5. **No magic strings.** Severity tiers via `SeverityTier` enum. Collection names via `settings.incidents_collection`. Stage names via the AGENT_STAGES constant.

6. **Explicit error handling.** Every agent node has `try/except`. On exception: set `state["error"]`, log the error, transition to `error_handler` node. Never let exceptions propagate to the API layer unhandled.

7. **Secrets only via settings.** Never hardcode API keys. Every key read via `pydantic-settings` from environment. `settings.gemini_api_key`, never `os.environ["GEMINI_API_KEY"]` scattered through code.

8. **Formatting.** Run `black backend/` before every commit. Run `ruff check backend/ --fix` before every commit. Both configured in `pyproject.toml`.

9. **Tests first for tools.** Every tool function has at least 2 unit tests in `tests/test_tools.py` covering the happy path and one edge case before the tool is wired into the agent graph.

10. **No fire-and-forget.** All background tasks registered via FastAPI `BackgroundTasks`. No bare `asyncio.create_task()` without proper error handling.

### TypeScript (frontend)

1. **No `any`.** Use `unknown` for genuinely unknown types, then narrow with type guards. Propagate proper types from `lib/types.ts`.

2. **Centralized API calls.** All `fetch` calls go through functions in `lib/api.ts`. Components never call `fetch` directly. Use TanStack Query mutations for POST, queries for GET.

3. **SSE in hooks only.** `EventSource` is only instantiated in `hooks/useSSE.ts`. Components consume the hook, never the EventSource.

4. **State in Zustand.** Analysis results, alert list, and current analysis state live in `store/sentinel.ts`. Component-local `useState` only for UI state (dropdown open, tab selected).

5. **`cn()` for all classes.** Never string concatenation for conditional classes. Always `cn('base-class', condition && 'conditional-class')`.

6. **Typed component props.** Every component has an `interface Props {}` or `type Props = {}`. No prop typing via `any` or inline objects.

7. **No inline styles.** All styling via Tailwind utility classes or CSS variables. No `style={{ color: '#FF3B30' }}` — use `text-severity-critical` instead.

8. **Accessibility.** All icon-only buttons have `aria-label`. All form fields have associated `<label>`. Severity badges use `role="status"` for screen readers. Respect `prefers-reduced-motion` in all animations.

9. **ESLint + Prettier on save.** Configure in `.eslintrc.json` and `.prettierrc`. Run `npm run lint` before commit.

10. **Mobile first.** All layouts start with mobile breakpoint. Use `md:`, `lg:` modifiers to expand. Never `max-md:` to restrict. Test at 375px before any desktop testing.

### Git Hygiene

- `.env` and `.env.local` in `.gitignore` — only `.env.example` and `.env.local.example` committed
- Branch naming: `feat/`, `fix/`, `chore/` prefixes
- Commit format: `feat(analyze): add SSE streaming endpoint`
- No direct commits to `main` — all changes via PR
- PR requires: lint passing + all tests green

---

## 12. Deployment Guide

### Step 1 — External Services Setup

**Qdrant Cloud (qdrant.io):**
1. Sign up free → Create cluster → Copy URL + API key
2. Run `python scripts/ingest_corpus.py` locally (point to cloud cluster)
3. Run `python scripts/seed_regulatory.py` locally
4. Collections now populated. Render just connects to them.

**Supabase (supabase.com):**
1. New project → copy URL + anon key + DB connection string
2. Run `alembic upgrade head` locally with `DATABASE_URL` set

**Upstash Redis (console.upstash.com):**
1. Create database → REST mode → copy URL + token

**Groq (console.groq.com):**
Create account → API Keys → Create new key

**Gemini (aistudio.google.com):**
Sign in with Google → "Get API key" → Create key in new project

### Step 2 — Render.com (Backend)

1. New Web Service → Connect GitHub repo → Root: `backend/`
2. Build command: `pip install -r requirements.txt && python -m spacy download en_core_web_lg`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Plan: Free tier (sufficient for demo)
5. Add all environment variables from `backend/.env.example` in the Environment tab
6. Deploy → copy the URL (e.g. `https://sentinel-api.onrender.com`)

**UptimeRobot (uptimerobot.com) — keep Render warm:**
1. Create free account → New Monitor
2. Type: HTTP(s), URL: `https://sentinel-api.onrender.com/health`
3. Interval: 14 minutes
4. This prevents Render free tier cold starts during the demo

### Step 3 — Vercel (Frontend)

1. vercel.com → New Project → Import GitHub repo → Root: `frontend/`
2. Framework: Next.js (auto-detected)
3. Add environment variable: `NEXT_PUBLIC_API_URL=https://sentinel-api.onrender.com`
4. Deploy → copy the URL

### Step 4 — GitHub Actions CI/CD

**`.github/workflows/deploy-backend.yml`:**
```yaml
name: Deploy Backend to Render
on:
  push:
    branches: [main]
    paths: ['backend/**']
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Trigger Render Deploy
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
          RENDER_SERVICE_ID: ${{ secrets.RENDER_SERVICE_ID }}
        run: |
          curl -X POST \
            "https://api.render.com/v1/services/$RENDER_SERVICE_ID/deploys" \
            -H "Authorization: Bearer $RENDER_API_KEY" \
            -H "Content-Type: application/json"
```

Vercel auto-deploys from GitHub on `main` push — no workflow needed.

### Deployment Checklist

- [ ] Qdrant cluster created + corpus ingested
- [ ] Supabase project created + migrations run
- [ ] Upstash Redis created
- [ ] All env vars added to Render
- [ ] UptimeRobot monitor active
- [ ] `NEXT_PUBLIC_API_URL` set in Vercel
- [ ] Frontend CORS origin added to backend `CORS_ORIGINS` env var
- [ ] Health endpoint returns 200: `curl https://sentinel-api.onrender.com/health`
- [ ] Sample analysis runs end-to-end in production

---

## 13. Testing Checklist

**Unit tests — run `pytest backend/tests/ -v`:**
- [ ] `test_compute_risk_score` — verify formula with known inputs, check all 4 components
- [ ] `test_classify_severity` — CRITICAL/HIGH/MEDIUM/LOW keyword detection
- [ ] `test_hybrid_search` — RRF merging produces correct ranked order
- [ ] `test_detect_precursor_patterns` — pattern matching with mock historical data
- [ ] `test_parse_incident_report` — Pydantic output parser handles LLM JSON response
- [ ] `test_rate_limit_middleware` — 11th request from same IP returns 429
- [ ] `test_cache_hit` — identical PDF hash returns cached analysis_id

**End-to-end tests (manual before demo):**
- [ ] Upload real OSHA PDF → full analysis completes in < 45 seconds
- [ ] Upload same PDF twice → second run returns instantly (cache hit)
- [ ] Upload a `.docx` file → 400 error with "Only PDF files supported"
- [ ] Upload an empty text file renamed to `.pdf` → 400 "File appears to be empty"
- [ ] Upload a PDF with only 50 words → analysis completes with low_confidence flag
- [ ] All 7 pipeline nodes show correct states (idle → active → complete) in sequence
- [ ] Dashboard stats reflect completed analyses
- [ ] Incident explorer filter by CRITICAL severity works
- [ ] Mobile layout at 375px width: no horizontal overflow, all text readable
- [ ] CRITICAL analysis: pulse animation visible on RiskCard
- [ ] "Try a sample report" CTA loads and runs the sample PDF
- [ ] Download PDF summary button works (even if it's just opening the report JSON for now)

---

## 14. Demo Script

### Pre-Demo Setup (5 minutes before)

1. Open `https://your-app.vercel.app` in Chrome, full screen, 1920×1080
2. Pre-warm backend: open `https://sentinel-api.onrender.com/health` in a background tab
3. Run one analysis on the sample report to warm the cache — note the analysis ID
4. Refresh to `/dashboard` — stats should show at least 1 completed analysis
5. Have the OSHA refinery incident PDF ready to drag in (pre-download it)

### Demo Flow (5 minutes total)

**Dashboard (45 seconds):**
Show the 4 stat cards, point to the severity chart and industry heatmap.
"This is SENTINEL — it doesn't just classify past incidents. It detects the early warning patterns that predict future ones, and cross-references every finding against real regulatory standards."

**Upload and analyze (2 minutes):**
Drag the OSHA PDF into the upload zone. Press "Run Analysis."
Point to the PipelineVisual as nodes activate one by one.
Name each stage live: "Routing the document type... now parsing structured incident data with Gemini... entity extraction via spaCy NER... running hybrid BM25 plus semantic search across 80 real historical incidents... regulatory audit against OSHA 29 CFR... computing the risk score — that's pure Python, no LLM guessing..."

**Results walkthrough (2 minutes):**
- Risk gauge: "This is a multi-dimensional score — severity, frequency of similar historical cases, regulatory violations, and precursor density. Each component is visible and explainable."
- Precursor list: "These 4 patterns appear in 9 or more historical incidents in our corpus. That's the detection. SENTINEL isn't just telling you what happened — it's telling you this exact combination of factors has preceded incidents before."
- Regulatory cards: "Every violation is a retrieved clause from the actual OSHA standard — not a hallucination. The system can't generate a regulation that isn't in the corpus."
- Action list: "Corrective actions sorted by urgency. Immediate actions at the top with regulatory references."

**Incident explorer (15 seconds):**
Navigate to `/incidents`. Show the filter by CRITICAL severity.
"Every analysis is persisted. Safety teams can track risk trends across their reports over time."

### Technical Talking Points (for technical judges)

> "Retrieval is BM25 sparse plus Qdrant dense vectors, merged with Reciprocal Rank Fusion, then cross-encoder reranked with FlashRank. That's three layers of retrieval quality control that standard RAG doesn't have."

> "The risk score is a pure Python algorithm — four weighted components, fully deterministic. The LLM doesn't touch it. Judges see the math."

> "LangGraph state machine with a typed TypedDict state passing between every agent node. Conditional edge after the risk scorer — CRITICAL analyses go through a priority synthesis path."

> "We use Gemini 2.0 Flash for reasoning — 1 million tokens per minute free tier. Groq llama-3.1-8b for fast tool calls — 131k TPM. Neither rate limits during a demo."

> "80 real incident reports from OSHA, CSB, and NIOSH. Not synthetic data."

---

*PRD v1.0 — SENTINEL Hackathon Edition*
*Architecture locked. UI design system defined. All tools free and verified.*
*Next: Figma UI design → implementation.*
