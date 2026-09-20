"""Shared assembly for both alert-synthesis paths.

The two synthesizer nodes differ in substance, not wording: the priority path
spends an LLM call writing a specific, quotable alert and reports every detected
precursor, while the standard path assembles a deterministic summary and reports
only the corroborated ones.
"""

from __future__ import annotations

import time

from ...llm import LLMUnavailable, complete_text
from ...models import (
    Alert,
    AnalysisReport,
    CausalEvent,
    CorrAction,
    HazardEntity,
    IncidentReport,
    PrecursorPattern,
    RegulatoryClause,
    RiskScore,
    SimilarIncident,
)
from ...tools import generate_corrective_actions
from ..state import SentinelState

# Standard path only surfaces patterns other incidents also showed.
STANDARD_MIN_EVIDENCE = 1


async def synthesize(
    state: SentinelState, *, priority: bool
) -> tuple[Alert, list[CorrAction], AnalysisReport]:
    incident = IncidentReport.model_validate(state["incident"] or {})
    risk = RiskScore.model_validate(state["risk_score"])
    clauses = [RegulatoryClause.model_validate(item) for item in state.get("regulatory_clauses", [])]
    patterns = [PrecursorPattern.model_validate(item) for item in state.get("precursor_patterns", [])]
    if not priority:
        patterns = [p for p in patterns if p.evidence_count >= STANDARD_MIN_EVIDENCE] or patterns

    actions = await generate_corrective_actions(
        state.get("hazard_type", "general"),
        precursors=patterns,
        clauses=clauses,
        summary=incident.sequence_of_events or state["raw_text"][:2000],
    )
    alert = Alert(
        severity=risk.tier,
        title=_title(incident, risk, priority=priority),
        description=await _description(incident, risk, patterns, clauses, priority=priority),
        regulatory_violations=[f"{c.regulation_name} {c.section}".strip() for c in clauses],
        precursor_patterns=[pattern.pattern_name for pattern in patterns],
    )
    report = AnalysisReport(
        analysis_id=state["analysis_id"],
        file_name=state["file_name"],
        incident=incident,
        entities=[HazardEntity.model_validate(item) for item in state.get("entities", [])],
        similar_incidents=[SimilarIncident.model_validate(i) for i in state.get("similar_incidents", [])],
        regulatory_clauses=clauses,
        precursor_patterns=patterns,
        causal_chain=[CausalEvent.model_validate(item) for item in state.get("causal_chain", [])],
        risk_score=risk,
        alerts=[alert],
        corrective_actions=actions,
        warnings=state.get("warnings", []),
        processing_time_seconds=round(time.monotonic() - state["started_at"], 2),
    )
    return alert, actions, report


def _title(incident: IncidentReport, risk: RiskScore, *, priority: bool) -> str:
    subject = incident.industry or "Workplace"
    prefix = "CRITICAL precursor risk" if priority else f"{risk.tier.value} risk"
    return f"{prefix}: {subject} incident scored {risk.total}/10"


def _deterministic_description(
    incident: IncidentReport,
    risk: RiskScore,
    patterns: list[PrecursorPattern],
    clauses: list[RegulatoryClause],
) -> str:
    pattern_text = (
        ", ".join(f"{p.pattern_name} (seen in {p.evidence_count} historical incidents)" for p in patterns)
        or "no corroborated precursor patterns"
    )
    clause_text = ", ".join(c.regulation_name for c in clauses) or "no matching clauses retrieved"
    return (
        f"{risk.explanation} Detected precursors: {pattern_text}. "
        f"Applicable standards: {clause_text}. "
        f"Reported outcome: {incident.injury_count} injured, {incident.fatality_count} fatal."
    )


async def _description(
    incident: IncidentReport,
    risk: RiskScore,
    patterns: list[PrecursorPattern],
    clauses: list[RegulatoryClause],
    *,
    priority: bool,
) -> str:
    deterministic = _deterministic_description(incident, risk, patterns, clauses)
    if not priority:
        return deterministic
    try:
        return await complete_text(
            [
                (
                    "system",
                    "Write a three-sentence safety alert for a plant manager. State what "
                    "happened, which precursor conditions predict a repeat, and what is at "
                    "stake. Use only the facts given. Do not cite any regulation not listed.",
                ),
                (
                    "human",
                    f"Incident: {incident.sequence_of_events}\n"
                    f"Risk: {risk.total}/10 ({risk.tier.value})\n"
                    f"Precursors: {', '.join(p.pattern_name for p in patterns) or 'none'}\n"
                    f"Standards: {', '.join(c.regulation_name for c in clauses) or 'none'}",
                ),
            ]
        )
    except LLMUnavailable:
        return deterministic
