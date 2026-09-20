"""Compute the risk score. Pure Python -- the LLM never touches this number."""

from __future__ import annotations

from ...models import IncidentReport, RegulatoryClause
from ...tools import corpus_size, known_precursor_count, score_incident, violated_clause_families
from ..state import SentinelState
from .base import NodeResult, node


@node("risk_scorer", "Computing multi-dimensional risk score...")
async def risk_scorer(state: SentinelState) -> NodeResult:
    incident = IncidentReport.model_validate(state["incident"] or {})
    clauses = [RegulatoryClause.model_validate(item) for item in state.get("regulatory_clauses", [])]
    hazard_type = state.get("hazard_type", "general")

    # Distinct source documents, not chunks: one report split into eight chunks
    # is one similar incident, and corpus_size counts documents.
    matched_documents = {item.get("source_document") for item in state.get("similar_incidents", [])} - {
        None
    }

    score = score_incident(
        incident,
        similar_count=len(matched_documents),
        corpus_size=corpus_size(),
        violated_clauses=violated_clause_families(clauses),
        detected_precursors=len(state.get("precursor_patterns", [])),
        known_precursors=known_precursor_count(hazard_type),
    )

    return NodeResult(
        updates={"risk_score": score.model_dump(mode="json")},
        message=f"Risk score {score.total}/10 - {score.tier.value}",
        data={"total": score.total, "tier": score.tier.value},
    )
