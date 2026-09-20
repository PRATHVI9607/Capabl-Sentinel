"""Semantic chunking and the cache client's two backends."""

from __future__ import annotations

import numpy as np
import pytest

from app.cache import client as cache
from app.config import settings
from app.rag import chunker
from tests.fixtures import HashingEncoder


@pytest.fixture
def embedder(monkeypatch):
    """Chunking needs sentence vectors; the hashing double gives real similarity."""
    encoder = HashingEncoder()
    monkeypatch.setattr(
        chunker, "embed_documents", lambda texts: np.asarray(list(encoder.embed(list(texts))))
    )


class TestSemanticChunking:
    def test_a_topic_shift_starts_a_new_chunk(self, embedder) -> None:
        lockout = " ".join(
            f"The lockout tagout isolation procedure for the press was not applied on step {n}."
            for n in range(6)
        )
        forklift = " ".join(
            f"A forklift struck a pedestrian near the warehouse loading dock in aisle {n}."
            for n in range(6)
        )
        chunks = chunker.semantic_chunks(f"{lockout} {forklift}")
        assert len(chunks) >= 2, "unrelated topics should not share a chunk"
        assert any("lockout" in c.text for c in chunks)
        assert any("forklift" in c.text for c in chunks)

    def test_one_topic_stays_in_one_chunk(self, embedder) -> None:
        text = " ".join(
            f"The lockout tagout isolation procedure for the press was skipped at stage {n}."
            for n in range(4)
        )
        assert len(chunker.semantic_chunks(text)) == 1

    def test_chunks_respect_the_word_budget(self, embedder) -> None:
        text = " ".join(f"Identical safety sentence number {n} about the press." for n in range(200))
        chunks = chunker.semantic_chunks(text)
        assert len(chunks) > 1
        # The budget is a soft boundary: a chunk closes once it is over, so one
        # sentence may carry it past. Nothing should run away, though.
        assert max(len(c.text.split()) for c in chunks) < chunker.MAX_WORDS * 2

    def test_section_headings_are_carried_onto_chunks(self, embedder) -> None:
        text = "FINDINGS\nThe guard was removed. The press cycled.\nCONCLUSIONS\nTraining was absent."
        sections = {chunk.section for chunk in chunker.semantic_chunks(text)}
        assert sections == {"FINDINGS", "CONCLUSIONS"}

    def test_metadata_is_attached_to_every_chunk(self, embedder) -> None:
        chunks = chunker.semantic_chunks("One sentence only.", metadata={"industry": "mining"})
        assert all(chunk.metadata["industry"] == "mining" for chunk in chunks)

    def test_metadata_is_not_shared_between_chunks(self, embedder) -> None:
        chunks = chunker.semantic_chunks(
            "A\nFINDINGS\nThe press cycled.\nCONCLUSIONS\nTraining was absent.",
            metadata={"industry": "mining"},
        )
        chunks[0].metadata["industry"] = "mutated"
        assert chunks[-1].metadata["industry"] == "mining"

    def test_empty_and_whitespace_input_produce_no_chunks(self, embedder) -> None:
        assert chunker.semantic_chunks("") == []
        assert chunker.semantic_chunks("   \n\n  ") == []

    def test_single_sentence_needs_no_embedding(self, monkeypatch) -> None:
        def explode(_texts):
            raise AssertionError("a single sentence must not be embedded")

        monkeypatch.setattr(chunker, "embed_documents", explode)
        assert len(chunker.semantic_chunks("Only one sentence here.")) == 1


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"result": self._payload}


class FakeClient:
    """Stands in for httpx.AsyncClient, recording the URLs the cache builds."""

    calls: list[tuple[str, dict]] = []
    payload: object = None
    error: Exception | None = None

    def __init__(self, **_: object) -> None:
        pass

    async def __aenter__(self) -> FakeClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def get(self, url: str, headers: dict) -> FakeResponse:
        FakeClient.calls.append((url, headers))
        if FakeClient.error:
            raise FakeClient.error
        return FakeResponse(FakeClient.payload)


@pytest.fixture
def upstash(monkeypatch):
    FakeClient.calls = []
    FakeClient.payload = None
    FakeClient.error = None
    monkeypatch.setattr(settings, "upstash_redis_rest_url", "https://fake.upstash.io/")
    monkeypatch.setattr(settings, "upstash_redis_rest_token", "tok")
    monkeypatch.setattr(cache.httpx, "AsyncClient", FakeClient)
    return FakeClient


class TestCacheRestBackend:
    async def test_get_builds_the_rest_path_and_authenticates(self, upstash) -> None:
        upstash.payload = "analysis-123"
        assert await cache.get("analysis:abc") == "analysis-123"
        url, headers = upstash.calls[0]
        assert url == "https://fake.upstash.io/get/analysis:abc"
        assert headers == {"Authorization": "Bearer tok"}

    async def test_missing_key_reads_as_none(self, upstash) -> None:
        upstash.payload = None
        assert await cache.get("absent") is None

    async def test_set_sends_the_ttl(self, upstash) -> None:
        await cache.set("k", "v", 3600)
        assert upstash.calls[0][0].endswith("/set/k/v/ex/3600")

    async def test_first_increment_also_sets_an_expiry(self, upstash) -> None:
        upstash.payload = 1
        assert await cache.incr_with_expiry("ratelimit:1.2.3.4", 3600) == 1
        paths = [url.split("upstash.io/")[1] for url, _ in upstash.calls]
        assert paths == ["incr/ratelimit:1.2.3.4", "expire/ratelimit:1.2.3.4/3600"]

    async def test_later_increments_do_not_reset_the_window(self, upstash) -> None:
        upstash.payload = 4
        assert await cache.incr_with_expiry("ratelimit:1.2.3.4", 3600) == 4
        assert len(upstash.calls) == 1

    async def test_an_outage_is_a_miss_not_a_failure(self, upstash) -> None:
        upstash.error = RuntimeError("upstash down")
        assert await cache.get("k") is None
        await cache.set("k", "v", 60)

    async def test_an_outage_never_locks_a_caller_out(self, upstash) -> None:
        upstash.error = RuntimeError("upstash down")
        # Returning 0 keeps the request flowing; failing closed would make a
        # cache outage look like a site outage.
        assert await cache.incr_with_expiry("ratelimit:1.2.3.4", 3600) == 0


class TestCacheLocalFallback:
    async def test_values_round_trip(self) -> None:
        await cache.set("k", "v", 60)
        assert await cache.get("k") == "v"

    async def test_expired_values_are_dropped(self, monkeypatch) -> None:
        await cache.set("k", "v", 60)
        monkeypatch.setattr(cache.time, "time", lambda: 1e12)
        assert await cache.get("k") is None

    async def test_counter_increments_within_one_window(self) -> None:
        counts = [await cache.incr_with_expiry("ip", 3600) for _ in range(3)]
        assert counts == [1, 2, 3]

    async def test_counter_restarts_after_the_window(self, monkeypatch) -> None:
        assert await cache.incr_with_expiry("ip", 3600) == 1
        monkeypatch.setattr(cache.time, "time", lambda: 1e12)
        assert await cache.incr_with_expiry("ip", 3600) == 1
