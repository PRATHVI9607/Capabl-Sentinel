"""The payloads the API hands to the frontend."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from .incident import HazardEntity, IncidentReport, SeverityTier
from .retrieval import RegulatoryClause, SimilarIncident
from .risk import CausalEvent, PrecursorPattern, RiskScore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Urgency(str, Enum):
    IMMEDIATE = "IMMEDIATE"
    SHORT_TERM = "SHORT_TERM"
    LONG_TERM = "LONG_TERM"


class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    severity: SeverityTier
    title: str
    description: str
    regulatory_violations: list[str] = Field(default_factory=list)
    precursor_patterns: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=_now)


class CorrAction(BaseModel):
    urgency: Urgency
    action: str
    rationale: str
    regulation_reference: str | None = None


class AnalysisReport(BaseModel):
    analysis_id: str
    file_name: str
    incident: IncidentReport
    entities: list[HazardEntity] = Field(default_factory=list)
    similar_incidents: list[SimilarIncident] = Field(default_factory=list)
    regulatory_clauses: list[RegulatoryClause] = Field(default_factory=list)
    precursor_patterns: list[PrecursorPattern] = Field(default_factory=list)
    causal_chain: list[CausalEvent] = Field(default_factory=list)
    risk_score: RiskScore
    alerts: list[Alert] = Field(default_factory=list)
    corrective_actions: list[CorrAction] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    processing_time_seconds: float = 0.0
    created_at: str = Field(default_factory=_now)


class AnalysisSummary(BaseModel):
    """Row shape for the history list -- the full report JSON is too big to page over."""

    analysis_id: str
    file_name: str
    status: str
    severity: SeverityTier
    risk_total: float
    industry: str | None = None
    created_at: str


class HistoryPage(BaseModel):
    items: list[AnalysisSummary]
    total: int
    page: int
    limit: int


class StreamUpdate(BaseModel):
    stage: str
    status: str = Field(description="'started' | 'completed' | 'error' | 'alive'")
    message: str = ""
    data: dict | None = None
    timestamp: str = Field(default_factory=_now)
