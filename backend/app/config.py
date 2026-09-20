"""Process-wide configuration, read once from the environment."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Every external credential is optional so the app still boots locally.

    A missing credential degrades one capability (no LLM, no vector store, no
    shared cache) instead of preventing startup.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM providers
    gemini_api_key: str = ""
    groq_api_key: str = ""
    # Floating aliases, not pinned versions. The PRD pinned gemini-2.0-flash and
    # llama-3.1-8b-instant; both were retired and returned 404 against a valid
    # key. An alias survives the provider rotating its models underneath us,
    # which matters more here than byte-identical reproducibility.
    gemini_model: str = "gemini-flash-latest"
    groq_model: str = "openai/gpt-oss-20b"

    # Vector store
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    incidents_collection: str = "sentinel_incidents"
    regulatory_collection: str = "sentinel_regulatory"

    # Persistence. SQLite by default so `uvicorn app.main:app` works with no setup.
    database_url: str = "sqlite+aiosqlite:///./sentinel.db"

    # Cache (Upstash REST). Falls back to an in-process dict when unset.
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""

    # Corpus, taxonomies and generated indexes.
    data_dir: Path = _BACKEND_ROOT / "data"

    # Retrieval / NLP models
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "ms-marco-TinyBERT-L-2-v2"
    # "blank" is a tokeniser plus our entity ruler, with no statistical model.
    # On real incident text the sm/lg NER adds only dates and cardinals, which
    # this domain has no use for -- see app/tools/parsing.py::_nlp. Set a real
    # pipeline name to layer it back on.
    spacy_model: str = "blank"

    # App
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"
    max_analyses_per_ip_per_hour: int = 10
    analysis_cache_ttl_seconds: int = 3600
    low_confidence_word_count: int = 100

    # Resource limits. Each one bounds work an anonymous caller can cause.
    max_upload_bytes: int = 10 * 1024 * 1024
    min_upload_bytes: int = 100
    max_pdf_pages: int = 300
    max_extracted_chars: int = 500_000
    analysis_timeout_seconds: int = 180
    stream_timeout_seconds: int = 300

    # Only trust X-Forwarded-For when a proxy you control sets it. On Render and
    # Vercel that is true; exposed directly to the internet it lets a caller
    # forge a client IP and bypass the rate limit.
    trust_proxy_headers: bool = False

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
