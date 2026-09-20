"""Terminal node for a failed run: emit what was produced before the failure.

Not wrapped with `@node` -- that decorator short-circuits on an existing error,
which is precisely the state this node exists to handle.
"""

from __future__ import annotations

import logging
import time

from ...models import (
    Alert,
    AnalysisReport,
    CausalEvent,
    HazardEntity,
    IncidentReport,
    PrecursorPattern,
    RegulatoryClause,
    RiskComponent,
    RiskScore,
    SeverityTier,
    SimilarIncident,
)
from ...tools import emit_stream_update
from ..state import SentinelState

logger = logging.getLogger(__name__)


def _unscored() -> RiskScore:
    return RiskScore(
        total=0.0,
        tier=SeverityTier.UNKNOWN,
        components=[
            RiskComponent(
                name=name, score=0.0, weight=weight, explanation="Not computed - analysis failed."
            )
            for name, weight in (
                ("Severity", 0.30),
                ("Frequency", 0.25),
                ("Regulatory", 0.25),
                ("Precursor Density", 0.20),
            )
        ],
        explanation="Risk score unavailable: the pipeline did not reach the scoring stage.",
    )


async def error_handler(state: SentinelState) -> dict:
    message = state.get("error") or "Unknown failure"
    logger.error("Analysis %s failed: %s", state.get("analysis_id"), message)

    risk = RiskScore.model_validate(state["risk_score"]) if state.get("risk_score") else _unscored()
    report = AnalysisReport(
        analysis_id=state["analysis_id"],
        file_name=state["file_name"],
        incident=IncidentReport.model_validate(state.get("incident") or {}),
        entities=[HazardEntity.model_validate(item) for item in state.get("entities", [])],
        similar_incidents=[SimilarIncident.model_validate(i) for i in state.get("similar_incidents", [])],
        regulatory_clauses=[
            RegulatoryClause.model_validate(c) for c in state.get("regulatory_clauses", [])
        ],
        precursor_patterns=[
            PrecursorPattern.model_validate(p) for p in state.get("precursor_patterns", [])
        ],
        causal_chain=[CausalEvent.model_validate(event) for event in state.get("causal_chain", [])],
        risk_score=risk,
        alerts=[
            Alert(
                severity=risk.tier,
                title="Analysis incomplete",
                description=f"SENTINEL stopped before finishing: {message}",
            )
        ],
        warnings=[*state.get("warnings", []), f"Partial result. {message}"],
        processing_time_seconds=round(time.monotonic() - state["started_at"], 2),
    )

    await emit_stream_update(state["analysis_id"], "error_handler", "error", message)
    return {"analysis_report": report.model_dump(mode="json"), "processing_stage": "error_handler"}
