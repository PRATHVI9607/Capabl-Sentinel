"""Models for everything that comes back out of the retrieval layer."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    """One reranked chunk, carrying enough metadata to cite it in the UI."""

    chunk_id: str
    text: str
    score: float
    source_document: str
    section: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)


class SimilarIncident(BaseModel):
    doc_id: str
    title: str
    industry: str = "unknown"
    severity: str = "UNKNOWN"
    similarity_score: float
    chunk_excerpt: str
    source_document: str
    incident_date: str | None = None
    hazard_tags: list[str] = Field(default_factory=list)


class RegulatoryClause(BaseModel):
    clause_id: str
    regulation_name: str = Field(description="e.g. 'OSHA 29 CFR 1910.147'")
    section: str
    clause_text: str
    violation_confidence: float = Field(ge=0.0, le=1.0)
    relevance_explanation: str
