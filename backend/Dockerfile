# SENTINEL backend for Hugging Face Spaces (Docker SDK, free CPU tier).
#
# Spaces gives 2 vCPU and 16GB RAM free, against Render free's 0.1 vCPU and
# 512MB. The embedder and reranker are CPU-bound, so that is the difference
# between one analysis at a time and several.
#
# Local use is identical:
#   docker build -t sentinel backend/
#   docker run -p 7860:7860 --env-file backend/.env sentinel

FROM python:3.11-slim

# Spaces runs containers as UID 1000. Everything the app writes -- the model
# caches, the SQLite file -- has to be owned by that user or startup fails on a
# permission error that looks like a model download problem.
RUN useradd -m -u 1000 sentinel

WORKDIR /app

# Dependencies first so a code change does not reinstall them.
COPY --chown=sentinel:sentinel requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY --chown=sentinel:sentinel app ./app
COPY --chown=sentinel:sentinel scripts ./scripts
COPY --chown=sentinel:sentinel data ./data

# WORKDIR creates /app as root, and --chown only covers the copied files. The
# app writes sentinel.db and the model caches into this directory, so the
# directory itself has to be owned too or startup dies on a permission error.
RUN chown -R sentinel:sentinel /app

USER sentinel

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/app \
    ENVIRONMENT=production \
    # Spaces sits behind its own proxy, so the forwarded address is the real
    # client and the rate limit should key on it.
    TRUST_PROXY_HEADERS=true \
    # SQLite on the container filesystem. It resets when the Space restarts;
    # set DATABASE_URL to a Postgres instance if history must survive.
    DATABASE_URL=sqlite+aiosqlite:////app/sentinel.db

# fastembed and flashrank download their models on first use into data/, which
# is writable above. Warming them at build time means the first request after a
# restart is fast instead of a 30-second download.
RUN python -c "from app.rag.embedder import embed_query; embed_query('warm')" \
 && python -c "from app.rag.retriever import _reranker; _reranker()" \
 || echo "model warm-up skipped; they will download on first request"

# Spaces routes public traffic to 7860.
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:7860/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
