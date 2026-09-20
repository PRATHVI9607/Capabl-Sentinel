"""Security behaviour of the public surface.

Each test corresponds to a control in the code, so removing the control breaks
a test rather than going unnoticed.
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from app.api.analyze import safe_filename
from app.config import settings
from app.ingest.loader import load_pdf
from app.main import SECURITY_HEADERS, app, client_ip

UNPARSEABLE_PDF = b"%PDF-1.4\n" + b"0" * 256


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def upload(client: TestClient, name: str, content: bytes, **kwargs):
    return client.post("/analyze", files={"file": (name, io.BytesIO(content), "application/pdf")}, **kwargs)


class TestFilenameHandling:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("../../etc/passwd.pdf", "passwd.pdf"),
            ("..\\..\\windows\\system32\\evil.pdf", "evil.pdf"),
            ("/absolute/path/report.pdf", "report.pdf"),
            ("report<img src=x onerror=alert(1)>.pdf", "report_img src_x onerror_alert_1_.pdf"),
            # The closing tag contains a slash, so path stripping takes it first.
            ("report<script>alert(1)</script>.pdf", "script_.pdf"),
            ("report\x00truncate.pdf", "report_truncate.pdf"),
            ("", "upload.pdf"),
            ("...", "upload.pdf"),
        ],
    )
    def test_directory_and_markup_are_stripped(self, raw: str, expected: str) -> None:
        assert safe_filename(raw) == expected

    def test_absurdly_long_names_are_truncated(self) -> None:
        assert len(safe_filename("a" * 5000 + ".pdf")) == 200

    def test_stored_name_is_the_sanitised_one(self, client: TestClient) -> None:
        analysis_id = upload(client, "../../../etc/report.pdf", UNPARSEABLE_PDF).json()["analysis_id"]
        rows = client.get("/history").json()["items"]
        assert all(".." not in row["file_name"] for row in rows)
        assert analysis_id


class TestUploadLimits:
    def test_oversized_body_is_refused(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr(settings, "max_upload_bytes", 4096)
        response = upload(client, "big.pdf", b"%PDF-1.4" + b"0" * 20_000)
        assert response.status_code == 413

    def test_content_type_is_not_trusted_over_the_magic_number(self, client: TestClient) -> None:
        # Claims to be a PDF by name and MIME type, but is not one.
        response = upload(client, "payload.pdf", b"<?php system($_GET[0]); ?>" * 20)
        assert response.status_code == 400
        assert "not a valid PDF" in response.json()["detail"]

    def test_pdf_page_budget_is_enforced(self, tmp_path, monkeypatch) -> None:
        from fpdf import FPDF

        monkeypatch.setattr(settings, "max_pdf_pages", 3)
        pdf = FPDF()
        for index in range(10):
            pdf.add_page()
            pdf.set_font("Helvetica", size=11)
            pdf.cell(0, 10, f"page {index} of an oversized report")
        path = tmp_path / "many-pages.pdf"
        path.write_bytes(bytes(pdf.output()))

        assert len(load_pdf(path)) == 3

    def test_character_budget_stops_extraction_early(self, tmp_path, monkeypatch) -> None:
        from fpdf import FPDF

        monkeypatch.setattr(settings, "max_extracted_chars", 200)
        pdf = FPDF()
        for _ in range(10):
            pdf.add_page()
            pdf.set_font("Helvetica", size=11)
            pdf.multi_cell(0, 6, "lockout tagout procedure text repeated. " * 40)
        path = tmp_path / "wordy.pdf"
        path.write_bytes(bytes(pdf.output()))

        pages = load_pdf(path)
        assert len(pages) < 10


class TestResponseHeaders:
    def test_security_headers_are_present_on_every_response(self, client: TestClient) -> None:
        headers = client.get("/health").headers
        for header, value in SECURITY_HEADERS.items():
            assert headers[header] == value

    def test_headers_survive_an_error_response(self, client: TestClient) -> None:
        response = client.get("/analyze/unknown-id")
        assert response.status_code == 404
        assert response.headers["X-Content-Type-Options"] == "nosniff"


class TestCors:
    def test_unlisted_origin_is_not_reflected(self, client: TestClient) -> None:
        response = client.get("/health", headers={"Origin": "https://evil.example"})
        assert response.headers.get("access-control-allow-origin") != "https://evil.example"

    def test_allowed_origin_is_echoed(self, client: TestClient) -> None:
        allowed = settings.cors_origin_list[0]
        response = client.get("/health", headers={"Origin": allowed})
        assert response.headers.get("access-control-allow-origin") == allowed

    def test_credentials_are_not_permitted(self, client: TestClient) -> None:
        allowed = settings.cors_origin_list[0]
        response = client.get("/health", headers={"Origin": allowed})
        assert "access-control-allow-credentials" not in response.headers


class TestRateLimitSpoofing:
    def test_forwarded_header_is_ignored_unless_trusted(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr(settings, "trust_proxy_headers", False)
        monkeypatch.setattr(settings, "max_analyses_per_ip_per_hour", 2)
        codes = [
            upload(client, "r.pdf", UNPARSEABLE_PDF, headers={"X-Forwarded-For": f"10.0.0.{n}"}).status_code
            for n in range(3)
        ]
        # A rotating forwarded address must not buy extra requests.
        assert codes[2] == 429

    def test_forwarded_header_is_used_when_trusted(self, monkeypatch) -> None:
        monkeypatch.setattr(settings, "trust_proxy_headers", True)
        request = _FakeRequest({"x-forwarded-for": "203.0.113.7, 10.0.0.1"}, host="10.0.0.1")
        assert client_ip(request) == "203.0.113.7"

    def test_direct_peer_is_used_when_not_trusted(self, monkeypatch) -> None:
        monkeypatch.setattr(settings, "trust_proxy_headers", False)
        request = _FakeRequest({"x-forwarded-for": "203.0.113.7"}, host="10.0.0.1")
        assert client_ip(request) == "10.0.0.1"

    def test_rate_limited_response_tells_the_caller_when_to_retry(
        self, client: TestClient, monkeypatch
    ) -> None:
        monkeypatch.setattr(settings, "max_analyses_per_ip_per_hour", 0)
        response = upload(client, "r.pdf", UNPARSEABLE_PDF)
        assert response.status_code == 429
        assert response.headers["Retry-After"] == "3600"


class TestErrorDisclosure:
    def test_pipeline_failure_does_not_leak_internals(self, client: TestClient, monkeypatch) -> None:
        secret_path = r"C:\secrets\service-account.json"

        def explode(*_args, **_kwargs):
            raise RuntimeError(f"could not open {secret_path}")

        monkeypatch.setattr("app.pipeline.load_pdf", explode)
        analysis_id = upload(client, "report.pdf", UNPARSEABLE_PDF).json()["analysis_id"]
        body = client.get(f"/analyze/{analysis_id}/stream").text

        assert "secrets" not in body
        assert "Analysis failed" in body

    def test_node_failure_reports_only_the_stage_and_exception_type(
        self, client: TestClient, monkeypatch
    ) -> None:
        def explode(*_args, **_kwargs):
            raise ValueError("connection string postgres://user:hunter2@host/db")

        monkeypatch.setattr("app.ingest.classifier.score_keywords", explode)
        analysis_id = upload(client, "report.pdf", UNPARSEABLE_PDF).json()["analysis_id"]
        body = client.get(f"/analyze/{analysis_id}/stream").text

        assert "hunter2" not in body


class _FakeRequest:
    """The two attributes `client_ip` reads, without standing up a real request."""

    def __init__(self, headers: dict[str, str], host: str) -> None:
        self.headers = headers
        self.client = type("Client", (), {"host": host})()


class TestBudgetsAreScopedToUploads:
    """The upload budgets must not silently truncate trusted corpus documents."""

    @staticmethod
    def _pdf(tmp_path, pages: int):
        from fpdf import FPDF

        pdf = FPDF()
        for index in range(pages):
            pdf.add_page()
            pdf.set_font("Helvetica", size=11)
            pdf.cell(0, 10, f"page {index} of a long investigation report")
        path = tmp_path / "long.pdf"
        path.write_bytes(bytes(pdf.output()))
        return path

    def test_upload_path_applies_the_configured_page_budget(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(settings, "max_pdf_pages", 3)
        assert len(load_pdf(self._pdf(tmp_path, 10))) == 3

    def test_an_explicit_budget_overrides_the_upload_default(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(settings, "max_pdf_pages", 3)
        assert len(load_pdf(self._pdf(tmp_path, 10), max_pages=50)) == 10

    def test_ingestion_reads_documents_the_upload_path_would_truncate(self, tmp_path, monkeypatch) -> None:
        import sys

        sys.path.insert(0, str(settings.data_dir.parent / "scripts"))
        from _ingest_common import INGEST_MAX_CHARS, INGEST_MAX_PAGES

        monkeypatch.setattr(settings, "max_pdf_pages", 3)
        monkeypatch.setattr(settings, "max_extracted_chars", 100)
        assert settings.max_pdf_pages < INGEST_MAX_PAGES
        assert settings.max_extracted_chars < INGEST_MAX_CHARS
        pages = load_pdf(self._pdf(tmp_path, 10), max_pages=INGEST_MAX_PAGES, max_chars=INGEST_MAX_CHARS)
        assert len(pages) == 10
