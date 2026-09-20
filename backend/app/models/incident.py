"""Structured representation of a parsed safety incident."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SeverityTier(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class EntityType(str, Enum):
    HAZARD = "HAZARD"
    EQUIPMENT = "EQUIPMENT"
    CHEMICAL = "CHEMICAL"
    CONDITION = "CONDITION"
    UNSAFE_ACT = "UNSAFE_ACT"


class HazardEntity(BaseModel):
    text: str
    entity_type: EntityType
    confidence: float = Field(ge=0.0, le=1.0)
    source: str = Field(description="'spacy' or 'llm'")


class IncidentReport(BaseModel):
    """What the parser pulls out of the uploaded document.

    Every field is optional because real reports omit things; the extractor is
    instructed to leave a field empty rather than invent a value.
    """

    incident_date: str | None = None
    location: str | None = None
    industry: str | None = None
    equipment_involved: list[str] = Field(default_factory=list)
    sequence_of_events: str = ""
    immediate_causes: list[str] = Field(default_factory=list)
    root_causes: list[str] = Field(default_factory=list)
    injury_count: int = 0
    fatality_count: int = 0
    severity_indicator: SeverityTier = SeverityTier.UNKNOWN
    raw_text_length: int = 0
    extraction_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
