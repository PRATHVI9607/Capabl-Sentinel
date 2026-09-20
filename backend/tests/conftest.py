"""Test configuration. Runs before any app module is imported."""

from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
# The ingest scripts are importable so their classification logic can be tested.
sys.path.insert(0, str(BACKEND_ROOT / "scripts"))

# Point the app at throwaway infrastructure before app.config builds its Settings.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test-sentinel.db")
os.environ.setdefault("ENVIRONMENT", "test")
for unset in ("GEMINI_API_KEY", "GROQ_API_KEY", "QDRANT_URL", "UPSTASH_REDIS_REST_URL"):
    os.environ[unset] = ""

import contextlib  # noqa: E402
import sqlite3  # noqa: E402

import pytest  # noqa: E402

from app.cache import client as cache  # noqa: E402

TEST_DATABASE = BACKEND_ROOT / "test-sentinel.db"


@pytest.fixture(autouse=True)
def clean_cache():
    """The in-process cache fallback is module state; each test starts from empty."""
    cache.reset_local()
    yield
    cache.reset_local()


@pytest.fixture(autouse=True)
def clean_database():
    """Empty the analyses table so history assertions see only their own rows.

    Done over a separate sqlite3 connection rather than the async engine: the
    engine is bound to whichever event loop the test is using, and this runs
    outside one.
    """
    _truncate()
    yield


def _truncate() -> None:
    if not TEST_DATABASE.exists():
        return
    with sqlite3.connect(TEST_DATABASE) as connection:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='analyses'"
        ).fetchall()
        if tables:
            connection.execute("DELETE FROM analyses")


@pytest.fixture(scope="session", autouse=True)
def remove_test_database():
    yield
    from app.db.session import engine

    # Close pooled connections so Windows will let the file go.
    engine.sync_engine.dispose()
    with contextlib.suppress(OSError):
        TEST_DATABASE.unlink(missing_ok=True)
