"""HTTP contract tests. No external service is reachable in this configuration."""

from __future__ import annotations

import io

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

# Smallest byte string that passes upload validation: correct extension, magic
# number and length. pdfplumber will reject it, which is the failure path we want.
UNPARSEABLE_PDF = b"%PDF-1.4\n" + b"0" * 256


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def upload(client: TestClient, name: str, content: bytes, mime: str = "application/pdf"):
    return client.post("/analyze", files={"file": (name, io.BytesIO(content), mime)})


class TestHealth:
    def test_reports_configuration_state(self, client: TestClient) -> None:
        body = client.get("/health").json()
        assert body["status"] == "ok"
        assert body["llm_configured"] is False
        assert body["vector_store_backend"] == "local"
        assert isinstance(body["vector_store_ready"], bool)

    def test_readiness_reflects_whether_an_index_exists(
        self, client: TestClient, monkeypatch, tmp_path
    ) -> None:
        # /health reads the real data directory, so pin it: the answer must come
        # from the index, not from whether this machine happens to have a corpus.
        from app.rag import local_store

        monkeypatch.setattr(settings, "data_dir", tmp_path)
        local_store.load.cache_clear()
        assert client.get("/health").json()["vector_store_ready"] is False

        local_store.save("sentinel_incidents", ["c1"], np.ones((1, 384), dtype=np.float32), [{"text": "x"}])
        assert client.get("/health").json()["vector_store_ready"] is True
        local_store.load.cache_clear()


class TestUploadValidation:
    def test_non_pdf_extension_is_rejected(self, client: TestClient) -> None:
        response = upload(client, "report.docx", b"x" * 500, "application/msword")
        assert response.status_code == 400
        assert "Only PDF" in response.json()["detail"]

    def test_empty_file_is_rejected(self, client: TestClient) -> None:
        response = upload(client, "report.pdf", b"")
        assert response.status_code == 400
        assert "empty or corrupt" in response.json()["detail"]

    def test_pdf_extension_without_pdf_content_is_rejected(self, client: TestClient) -> None:
        response = upload(client, "report.pdf", b"plain text pretending to be a pdf" * 10)
        assert response.status_code == 400
        assert "not a valid PDF" in response.json()["detail"]

    def test_oversized_file_is_rejected(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr(settings, "max_upload_bytes", 1024)
        response = upload(client, "report.pdf", b"%PDF-1.4" + b"0" * 2048)
        assert response.status_code == 413


class TestAnalysisLifecycle:
    def test_accepted_upload_returns_an_id(self, client: TestClient) -> None:
        response = upload(client, "report.pdf", UNPARSEABLE_PDF)
        assert response.status_code == 202
        body = response.json()
        assert body["status"] == "processing"
        assert body["analysis_id"]

    def test_unreadable_pdf_fails_without_a_server_error(self, client: TestClient) -> None:
        analysis_id = upload(client, "report.pdf", UNPARSEABLE_PDF).json()["analysis_id"]
        # TestClient runs background tasks before returning, so the run is already over.
        assert client.get(f"/analyze/{analysis_id}").status_code == 404

    def test_stream_replays_the_failure_to_a_late_subscriber(self, client: TestClient) -> None:
        analysis_id = upload(client, "report.pdf", UNPARSEABLE_PDF).json()["analysis_id"]
        body = client.get(f"/analyze/{analysis_id}/stream").text
        assert '"status":"error"' in body

    def test_failed_analysis_is_not_cached(self, client: TestClient) -> None:
        first = upload(client, "report.pdf", UNPARSEABLE_PDF).json()
        second = upload(client, "report.pdf", UNPARSEABLE_PDF).json()
        assert second["analysis_id"] != first["analysis_id"]

    def test_a_cached_hash_short_circuits_the_pipeline(self, client: TestClient) -> None:
        import asyncio
        import hashlib

        from app.cache import client as cache
        from app.pipeline import cache_key

        digest = hashlib.sha256(UNPARSEABLE_PDF).hexdigest()
        asyncio.run(cache.set(cache_key(digest), "previous-id", 3600))

        body = upload(client, "report.pdf", UNPARSEABLE_PDF).json()
        assert body == {"analysis_id": "previous-id", "status": "cached"}

    def test_unknown_analysis_is_a_404(self, client: TestClient) -> None:
        assert client.get("/analyze/does-not-exist").status_code == 404


class TestRateLimit:
    def test_requests_beyond_the_hourly_cap_are_refused(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr(settings, "max_analyses_per_ip_per_hour", 2)
        codes = [upload(client, "report.pdf", UNPARSEABLE_PDF).status_code for _ in range(3)]
        assert codes[:2] == [202, 202]
        assert codes[2] == 429

    def test_reads_are_never_rate_limited(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr(settings, "max_analyses_per_ip_per_hour", 1)
        assert all(client.get("/health").status_code == 200 for _ in range(5))


class TestHistory:
    def test_empty_history_is_a_valid_page(self, client: TestClient) -> None:
        body = client.get("/history").json()
        assert body["items"] == []
        assert body["total"] == 0
        assert body["page"] == 1

    def test_stats_are_zeroed_not_missing(self, client: TestClient) -> None:
        body = client.get("/history/stats").json()
        assert set(body) == {
            "total_analyses",
            "critical_alerts",
            "avg_risk_score",
            "industries_covered",
        }

    def test_page_size_is_bounded(self, client: TestClient) -> None:
        assert client.get("/history", params={"limit": 1000}).status_code == 422

    def test_invalid_severity_filter_is_rejected(self, client: TestClient) -> None:
        assert client.get("/history", params={"severity": "SEVERE"}).status_code == 422


class TestToolIntrospection:
    def test_all_ten_tools_are_listed_with_schemas(self, client: TestClient) -> None:
        tools = client.get("/tools").json()
        assert len(tools) == 10
        assert {tool["name"] for tool in tools} == {
            "build_causal_chain",
            "classify_severity",
            "compute_risk_score",
            "detect_precursor_patterns",
            "emit_stream_update",
            "extract_hazard_entities",
            "generate_corrective_actions",
            "hybrid_search_incidents",
            "parse_incident_report",
            "retrieve_regulatory_clauses",
        }

    def test_every_tool_carries_a_description_and_parameters(self, client: TestClient) -> None:
        for tool in client.get("/tools").json():
            assert tool["description"], f"{tool['name']} has no description"
            assert tool["parameters"], f"{tool['name']} has no inferred parameters"

    def test_scoring_tool_exposes_the_formula_inputs(self, client: TestClient) -> None:
        tools = {tool["name"]: tool for tool in client.get("/tools").json()}
        assert tools["compute_risk_score"]["parameters"] == [
            "corpus_size",
            "detected_precursors",
            "known_precursors",
            "severity",
            "similar_count",
            "violated_clauses",
        ]
        assert tools["compute_risk_score"]["is_async"] is False
        assert tools["parse_incident_report"]["is_async"] is True


class TestConcurrencyLimit:
    """Analyses queue rather than exhausting a small instance's memory."""

    def test_a_second_upload_is_told_it_is_queued(self, client: TestClient, monkeypatch) -> None:
        import asyncio

        from app import pipeline

        # Hold the only slot so the next analysis has to wait for it.
        held = asyncio.Semaphore(1)
        monkeypatch.setattr(pipeline, "_slots", held)
        asyncio.get_event_loop_policy().new_event_loop().run_until_complete(held.acquire())

        analysis_id = upload(client, "report.pdf", UNPARSEABLE_PDF).json()["analysis_id"]
        body = client.get(f"/analyze/{analysis_id}/stream").text
        assert '"stage":"queued"' in body, "a waiting caller should be told, not left silent"

    def test_the_limit_is_configurable(self) -> None:
        # One by default because a free instance cannot embed twice at once.
        assert settings.max_concurrent_analyses >= 1
