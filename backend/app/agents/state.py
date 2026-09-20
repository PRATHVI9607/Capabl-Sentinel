"""The typed state every LangGraph node reads from and writes to."""

from __future__ import annotations

from typing import Literal, TypedDict

DocumentType = Literal["incident", "regulatory", "unknown"]


class SentinelState(TypedDict, total=False):
    """Nested values are stored as plain dicts so the state stays JSON-serialisable.

    Nodes validate back into the Pydantic models in `app.models` when they need
    typed access; the report assembled at the end is the authoritative shape.
    """

    # Input
    analysis_id: str
    file_name: str
    raw_text: str
    started_at: float

    # Pipeline output, filled in node order
    document_type: DocumentType
    incident: dict | None
    entities: list[dict]
    hazard_type: str
    similar_incidents: list[dict]
    precursor_patterns: list[dict]
    causal_chain: list[dict]
    regulatory_clauses: list[dict]
    risk_score: dict | None
    alerts: list[dict]
    corrective_actions: list[dict]
    analysis_report: dict | None

    # Control
    warnings: list[str]
    error: str | None
    processing_stage: str
    iteration_count: int


def initial_state(analysis_id: str, file_name: str, raw_text: str, started_at: float) -> SentinelState:
    return SentinelState(
        analysis_id=analysis_id,
        file_name=file_name,
        raw_text=raw_text,
        started_at=started_at,
        document_type="unknown",
        incident=None,
        entities=[],
        hazard_type="general",
        similar_incidents=[],
        precursor_patterns=[],
        causal_chain=[],
        regulatory_clauses=[],
        risk_score=None,
        alerts=[],
        corrective_actions=[],
        analysis_report=None,
        warnings=[],
        error=None,
        processing_stage="document_router",
        iteration_count=0,
    )
