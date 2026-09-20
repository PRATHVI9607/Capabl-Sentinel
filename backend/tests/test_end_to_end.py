"""Full pipeline over a real PDF.

A PDF is generated, uploaded through the HTTP API, and the resulting SSE stream
and persisted report are checked. Only two boundaries are stubbed: the sentence
embedder and the LLM providers. Everything else is production code -- pdfplumber,
preprocessing, semantic routing, hybrid retrieval, RRF, compression, scoring,
synthesis, SQLAlchemy and the SSE broker.
"""

from __future__ import annotations

import io
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from fpdf import FPDF

import app.agents.nodes.risk_scorer  # (populates sys.modules)
from app import llm
from app.config import settings
from app.ingest import classifier
from app.knowledge_graph import serializer
from app.main import app
from app.models import RiskComponent, RiskScore, SeverityTier
from app.rag import embedder, local_store, retriever, vector_store
from app.rag.bm25_index import BM25Index
from app.tools import actions, patterns, retrieval
from tests.fixtures import (
    LOCKOUT_INCIDENT_OVERRIDES,
    PRIORITY_ALERT_TEXT,
    FailingLLM,
    FakeLLM,
    HashingEncoder,
)

# `app.agents.nodes` re-exports each node function under its own module's name,
# so the package attribute shadows the module. Reach past it for monkeypatching.
RISK_SCORER_MODULE = sys.modules["app.agents.nodes.risk_scorer"]

REAL_DATA = Path(__file__).resolve().parent.parent / "data"
TAXONOMY_FILES = ("precursors.json", "actions.json", "entity_patterns.json")

REPORT_BODY = """
ACCIDENT INVESTIGATION SUMMARY

On March 14, 2023 a maintenance technician at a metal stamping plant in Rockford,
Illinois was fatally injured while clearing a jam from a 400 ton hydraulic press.

SEQUENCE OF EVENTS

The technician observed a misfeed on the infeed conveyor and reached into the die
area to clear a jam. The press had not been locked out and the machine was still
running. No lockout device had been applied to the disconnect. The technician did
not verify a zero energy state before entering the point of operation. The ram
cycled and the technician was pronounced dead at the scene.

FINDINGS

No written procedure existed for energy isolation on this press. The interlocked
guard on the die area had been bypassed some months earlier to speed up jam
clearing, and the bypass was never reported. Operators stated that production
pressure discouraged shutting the line down. The technician had not been trained
on the energy control procedure for this equipment.
"""

HISTORICAL_CHUNKS = [
    {
        "title": "Press operator amputation 2019",
        "hazard": "lockout_tagout",
        "text": (
            "The operator reached into the press to clear a jam while running. The crew "
            "did not verify zero energy before the work and no lockout had been applied. "
            "No written procedure existed for the machine."
        ),
    },
    {
        "title": "Conveyor entanglement 2020",
        "hazard": "lockout_tagout",
        "text": (
            "A maintenance worker cleared a jam on a conveyor. The machine was still "
            "running and the technician did not verify the isolation. Production pressure "
            "discouraged shutting down the line."
        ),
    },
    {
        "title": "Stamping press fatality 2021",
        "hazard": "lockout_tagout",
        "text": (
            "The die area guard was bypassed to clear a jam. No lockout was applied to the "
            "disconnect and the crew did not verify a zero energy state. The worker had not "
            "been trained on the procedure."
        ),
    },
    {
        "title": "Roll mill injury 2018",
        "hazard": "machine_guarding",
        "text": (
            "The guard removed from the roll mill was never replaced. The operator reached "
            "into the nip point while running to clear a jam."
        ),
    },
]

REGULATORY_CHUNKS = [
    {
        "regulation_name": "OSHA 29 CFR 1910.147",
        "section": "(c)(4)(i)",
        "text": (
            "Procedures shall be developed, documented and utilized for the control of "
            "potentially hazardous energy when employees are engaged in the activities "
            "covered by this section. The employer shall establish a program of lockout "
            "procedures before servicing a machine where unexpected energization could "
            "occur while clearing a jam."
        ),
    },
    {
        "regulation_name": "OSHA 29 CFR 1910.147",
        "section": "(d)(6)",
        "text": (
            "Prior to starting work the authorized employee shall verify that isolation and "
            "deenergization of the machine have been accomplished. The zero energy state "
            "shall be verified before any employee enters the point of operation."
        ),
    },
    {
        "regulation_name": "OSHA 29 CFR 1910.212",
        "section": "(a)(1)",
        "text": (
            "One or more methods of machine guarding shall be provided to protect the "
            "operator from hazards such as those created by point of operation, ingoing nip "
            "points and rotating parts. The guard shall not be bypassed while running."
        ),
    },
]

# What the seeded corpus stands in for; the frequency component divides by this.
PRETEND_CORPUS_SIZE = 80

CRITICAL_SCORE = RiskScore(
    total=9.1,
    tier=SeverityTier.CRITICAL,
    components=[
        RiskComponent(name="Severity", score=9.5, weight=0.30, explanation="fatality"),
        RiskComponent(name="Frequency", score=10.0, weight=0.25, explanation="saturated"),
        RiskComponent(name="Regulatory", score=8.4, weight=0.25, explanation="two families"),
        RiskComponent(name="Precursor Density", score=8.0, weight=0.20, explanation="8 of 10"),
    ],
    explanation="forced CRITICAL for the routing test",
)


# fpdf2 stamps CreationDate to the second, so two PDFs built from the same text
# a second apart differ in bytes -- and therefore in SHA-256, which is what the
# upload cache keys on. Pinning the date makes generated PDFs byte-identical.
FIXED_CREATION_DATE = datetime(2026, 1, 1, tzinfo=UTC)


def make_pdf(body: str) -> bytes:
    pdf = FPDF()
    pdf.set_creation_date(FIXED_CREATION_DATE)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, body.strip())
    return bytes(pdf.output())


def reset_caches() -> None:
    """Drop every cache keyed on the data directory or the corpus."""
    for cached in (
        patterns.taxonomy,
        actions._templates,
        retrieval.corpus_size,
        local_store.load,
        retriever._bm25_for,
        serializer.load,
    ):
        # A test may have replaced one of these with a plain stub.
        if clear := getattr(cached, "cache_clear", None):
            clear()


def seed_collection(data_dir: Path, collection: str, chunks: list[dict]) -> None:
    ids = [f"{collection}-{index}" for index, _ in enumerate(chunks)]
    texts = [chunk["text"] for chunk in chunks]
    vectors = embedder.embed_documents(texts)
    payloads = [
        {**chunk, "chunk_id": chunk_id, "text": text}
        for chunk_id, chunk, text in zip(ids, chunks, texts, strict=False)
    ]
    local_store.save(collection, ids, vectors, payloads)
    BM25Index.build(ids, texts).save(data_dir / f"bm25_{collection}.pkl")


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    """A throwaway data directory holding the taxonomies and a seeded corpus."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    for name in TAXONOMY_FILES:
        shutil.copy(REAL_DATA / name, data_dir / name)
    (data_dir / "corpus_manifest.json").write_text(
        json.dumps({"document_count": PRETEND_CORPUS_SIZE, "chunk_count": 2000}), encoding="utf-8"
    )

    monkeypatch.setattr(settings, "data_dir", data_dir)
    monkeypatch.setattr(embedder, "_model", lambda: HashingEncoder())
    reset_caches()

    seed_collection(data_dir, settings.incidents_collection, HISTORICAL_CHUNKS)
    seed_collection(data_dir, settings.regulatory_collection, REGULATORY_CHUNKS)
    reset_caches()
    yield data_dir
    reset_caches()


@pytest.fixture
def fake_llm(monkeypatch):
    llm_double = FakeLLM(LOCKOUT_INCIDENT_OVERRIDES, PRIORITY_ALERT_TEXT)
    monkeypatch.setattr(llm, "_providers", lambda *, fast: [("fake", llm_double)])
    # The classifier caches nothing, but it holds its own import of the helper.
    monkeypatch.setattr(classifier, "complete_structured", llm.complete_structured)
    return llm_double


@pytest.fixture
def client(corpus, fake_llm):
    with TestClient(app) as test_client:
        yield test_client


def analyse(client: TestClient, body: str = REPORT_BODY) -> dict:
    """Upload a report and return the final SSE payload."""
    response = client.post(
        "/analyze",
        files={"file": ("press-fatality.pdf", io.BytesIO(make_pdf(body)), "application/pdf")},
    )
    assert response.status_code == 202, response.text
    analysis_id = response.json()["analysis_id"]

    events = read_stream(client, analysis_id)
    assert events[-1]["stage"] == "complete", events[-1]
    # A partial report also arrives as "complete"; the error node must not have run.
    assert not [event for event in events if event["stage"] == "error_handler"], events
    return {"analysis_id": analysis_id, "events": events, "report": events[-1]["data"]}


def read_stream(client: TestClient, analysis_id: str) -> list[dict]:
    body = client.get(f"/analyze/{analysis_id}/stream").text
    return [
        json.loads(line.removeprefix("data: ")) for line in body.splitlines() if line.startswith("data: ")
    ]


class TestHappyPath:
    def test_every_stage_reports_start_then_completion_in_order(self, client: TestClient) -> None:
        result = analyse(client)
        events = result["events"]
        stages = [event["stage"] for event in events if event["status"] in {"started", "completed"}]
        synthesizer = (
            "priority_alert_synthesizer"
            if result["report"]["risk_score"]["total"] >= 8.0
            else "alert_synthesizer"
        )
        assert list(dict.fromkeys(stages)) == [
            "document_router",
            "incident_parser",
            "entity_extractor",
            "pattern_detector",
            "regulatory_auditor",
            "risk_scorer",
            synthesizer,
            "complete",
        ]
        # Each stage announces itself before it reports a result.
        for stage in stages[:-1]:
            started = stages.index(stage)
            assert events[started]["status"] == "started" or stage == "complete"
        assert not [event for event in events if event["status"] == "error"]

    def test_routing_follows_the_computed_score(self, client: TestClient) -> None:
        result = analyse(client)
        ran = {event["stage"] for event in result["events"]}
        critical = result["report"]["risk_score"]["total"] >= 8.0
        assert ("priority_alert_synthesizer" in ran) is critical
        assert ("alert_synthesizer" in ran) is not critical

    def test_incident_is_parsed_into_the_structured_report(self, client: TestClient) -> None:
        incident = analyse(client)["report"]["incident"]
        assert incident["industry"] == "manufacturing"
        assert incident["fatality_count"] == 1
        # Severity comes from the keyword rules over the real PDF text, not the LLM.
        assert incident["severity_indicator"] == "CRITICAL"
        assert "hydraulic press" in incident["equipment_involved"]

    def test_entities_combine_dictionary_matches_and_llm_discovery(self, client: TestClient) -> None:
        entities = analyse(client)["report"]["entities"]
        by_source = {entity["source"] for entity in entities}
        assert by_source == {"spacy", "llm"}, "both extraction paths should contribute"

        texts = {entity["text"].lower() for entity in entities}
        assert "press" in texts, "the entity ruler should match equipment"
        assert "disconnect" in texts, "the LLM should add what the dictionary misses"
        # The model also proposed an entity absent from the report; it must be dropped.
        assert not any("nobody wrote down" in text for text in texts)

    def test_historical_matches_come_back_with_their_source(self, client: TestClient) -> None:
        similar = analyse(client)["report"]["similar_incidents"]
        assert similar, "hybrid retrieval returned nothing from the seeded corpus"
        titles = {item["title"] for item in similar}
        assert titles & {chunk["title"] for chunk in HISTORICAL_CHUNKS}
        assert all(item["chunk_excerpt"] for item in similar)

    def test_precursors_are_reported_with_corroboration_counts(self, client: TestClient) -> None:
        patterns_found = analyse(client)["report"]["precursor_patterns"]
        assert patterns_found, "no precursor patterns detected"
        names = {pattern["pattern_name"] for pattern in patterns_found}
        assert "Verification step omitted" in names
        assert all(pattern["evidence_count"] >= 0 for pattern in patterns_found)
        assert all(0.0 <= pattern["confidence"] <= 1.0 for pattern in patterns_found)

    def test_every_clause_is_verbatim_from_the_regulatory_corpus(self, client: TestClient) -> None:
        clauses = analyse(client)["report"]["regulatory_clauses"]
        assert clauses, "regulatory retrieval returned nothing"
        seeded = " ".join(chunk["text"] for chunk in REGULATORY_CHUNKS)
        for clause in clauses:
            # Contextual compression trims sentences, so check sentence-wise containment.
            for sentence in clause["clause_text"].split(". "):
                assert sentence.strip(" .") in seeded, clause["clause_text"]
            assert clause["regulation_name"].startswith("OSHA 29 CFR")

    def test_risk_total_equals_its_own_components(self, client: TestClient) -> None:
        risk = analyse(client)["report"]["risk_score"]
        recomputed = round(sum(c["score"] * c["weight"] for c in risk["components"]), 2)
        assert risk["total"] == pytest.approx(recomputed, abs=0.01)
        assert [c["name"] for c in risk["components"]] == [
            "Severity",
            "Frequency",
            "Regulatory",
            "Precursor Density",
        ]
        assert 0.0 <= risk["total"] <= 10.0

    def test_critical_score_takes_the_priority_synthesis_path(
        self, client: TestClient, monkeypatch
    ) -> None:
        # The arithmetic has its own tests; this pins the conditional edge and the
        # behaviour that only the priority path has.
        monkeypatch.setattr(RISK_SCORER_MODULE, "score_incident", lambda *a, **k: CRITICAL_SCORE)
        result = analyse(client)
        report = result["report"]

        assert report["risk_score"]["tier"] == "CRITICAL"
        assert report["alerts"][0]["severity"] == "CRITICAL"
        # The priority path is the only one that asks the model to write the alert.
        assert report["alerts"][0]["description"] == PRIORITY_ALERT_TEXT
        assert any(event["stage"] == "priority_alert_synthesizer" for event in result["events"])
        assert not any(event["stage"] == "alert_synthesizer" for event in result["events"])

    def test_standard_path_writes_a_deterministic_alert(self, client: TestClient) -> None:
        report = analyse(client)["report"]
        if report["risk_score"]["total"] >= 8.0:
            pytest.skip("this corpus produced a CRITICAL score")
        description = report["alerts"][0]["description"]
        assert description != PRIORITY_ALERT_TEXT
        assert str(report["risk_score"]["total"]) in description

    def test_corrective_actions_lead_with_the_immediate_tier(self, client: TestClient) -> None:
        report = analyse(client)["report"]
        urgencies = [action["urgency"] for action in report["corrective_actions"]]
        assert urgencies, "no corrective actions produced"
        assert urgencies[0] == "IMMEDIATE"
        order = ["IMMEDIATE", "SHORT_TERM", "LONG_TERM"]
        assert [order.index(u) for u in urgencies] == sorted(order.index(u) for u in urgencies)
        # Templates for the detected hazard family, not a generic list.
        references = [
            a["regulation_reference"] for a in report["corrective_actions"] if a["regulation_reference"]
        ]
        assert references, "no action carried a regulation reference"
        assert any("1910.147" in reference for reference in references)

    def test_causal_chain_is_built_from_the_reported_causes(self, client: TestClient) -> None:
        chain = analyse(client)["report"]["causal_chain"]
        assert chain
        assert [event["order"] for event in chain] == list(range(len(chain)))
        assert any("verify" in event["label"].lower() for event in chain)

    def test_report_is_persisted_and_readable_afterwards(self, client: TestClient) -> None:
        result = analyse(client)
        fetched = client.get(f"/analyze/{result['analysis_id']}")
        assert fetched.status_code == 200
        assert fetched.json()["risk_score"]["total"] == result["report"]["risk_score"]["total"]

    def test_completed_analysis_appears_in_history_and_stats(self, client: TestClient) -> None:
        report = analyse(client)["report"]
        history = client.get("/history").json()
        assert history["total"] == 1
        assert history["items"][0]["severity"] == report["risk_score"]["tier"]
        row = history["items"][0]
        assert row["industry"] == "manufacturing"
        assert row["status"] == "complete"

        stats = client.get("/history/stats").json()
        assert stats["total_analyses"] == 1
        assert stats["industries_covered"] == 1
        assert stats["avg_risk_score"] == pytest.approx(row["risk_total"], abs=0.01)

    def test_processing_time_is_recorded(self, client: TestClient) -> None:
        assert analyse(client)["report"]["processing_time_seconds"] >= 0

    def test_identical_upload_is_served_from_cache(self, client: TestClient) -> None:
        first = analyse(client)
        again = client.post(
            "/analyze",
            files={"file": ("press-fatality.pdf", io.BytesIO(make_pdf(REPORT_BODY)), "application/pdf")},
        )
        assert again.json() == {"analysis_id": first["analysis_id"], "status": "cached"}


class TestDegradedInputs:
    def test_very_short_document_completes_with_a_low_confidence_warning(self, client: TestClient) -> None:
        report = analyse(client, "A worker slipped on a wet floor and was treated on site.")["report"]
        assert report["warnings"]
        assert any("low confidence" in warning.lower() for warning in report["warnings"])
        assert report["risk_score"]["total"] >= 0

    def test_provider_failure_falls_through_to_the_second_provider(
        self, client: TestClient, monkeypatch
    ) -> None:
        working = FakeLLM(LOCKOUT_INCIDENT_OVERRIDES, PRIORITY_ALERT_TEXT)
        monkeypatch.setattr(
            llm, "_providers", lambda *, fast: [("broken", FailingLLM()), ("working", working)]
        )
        report = analyse(client)["report"]
        assert report["incident"]["industry"] == "manufacturing"

    def test_no_provider_at_all_still_produces_a_scored_report(
        self, client: TestClient, monkeypatch
    ) -> None:
        monkeypatch.setattr(llm, "_providers", lambda *, fast: [])
        report = analyse(client)["report"]
        assert report["risk_score"]["tier"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"}
        assert report["incident"]["extraction_confidence"] < 0.5
        assert report["corrective_actions"]

    def test_empty_corpus_does_not_break_the_run(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr(vector_store, "search", lambda *a, **k: [])
        monkeypatch.setattr(vector_store, "fetch_payloads", lambda *a, **k: {})
        monkeypatch.setattr(retriever, "_bm25_for", lambda _collection: None)
        report = analyse(client)["report"]
        assert report["similar_incidents"] == []
        assert report["regulatory_clauses"] == []
        assert report["risk_score"]["components"][1]["score"] == 0.0


class TestRetrievalQuality:
    def test_hybrid_retrieval_ranks_the_matching_hazard_family_first(self, client: TestClient) -> None:
        similar = analyse(client)["report"]["similar_incidents"]
        lockout_titles = {c["title"] for c in HISTORICAL_CHUNKS if c["hazard"] == "lockout_tagout"}
        assert similar[0]["title"] in lockout_titles

    def test_compression_trims_the_retrieved_passage(self, client: TestClient) -> None:
        similar = analyse(client)["report"]["similar_incidents"]
        originals = {chunk["title"]: chunk["text"] for chunk in HISTORICAL_CHUNKS}
        assert any(
            len(item["chunk_excerpt"]) < len(originals[item["title"]])
            for item in similar
            if item["title"] in originals
        )

    def test_seeded_vectors_are_normalised(self, corpus) -> None:
        index = local_store.load(settings.incidents_collection)
        norms = np.linalg.norm(index.vectors, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-5)
