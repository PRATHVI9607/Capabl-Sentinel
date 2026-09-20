"""Risk scoring output. The numbers here come from pure Python, never an LLM."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .incident import SeverityTier


class RiskComponent(BaseModel):
    name: str
    score: float = Field(ge=0.0, le=10.0)
    weight: float = Field(ge=0.0, le=1.0)
    explanation: str


class PrecursorPattern(BaseModel):
    pattern_name: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_count: int = Field(ge=0, description="historical incidents showing this pattern")
    hazard_types: list[str] = Field(default_factory=list)


class CausalEvent(BaseModel):
    order: int
    label: str
    node_type: str
    relation: str = ""


class RiskScore(BaseModel):
    total: float = Field(ge=0.0, le=10.0)
    tier: SeverityTier
    components: list[RiskComponent]
    explanation: str
