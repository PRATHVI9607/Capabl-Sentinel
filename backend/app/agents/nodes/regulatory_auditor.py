"""Retrieve the regulatory clauses that apply to this incident."""

from __future__ import annotations

from ...models import IncidentReport
from ...tools import retrieve_regulatory_clauses, violated_clause_families
from ..state import SentinelState
from .base import NodeResult, node

CLAUSE_COUNT = 6


@node("regulatory_auditor", "Cross-referencing regulatory standards...")
async def regulatory_auditor(state: SentinelState) -> NodeResult:
    incident = IncidentReport.model_validate(state["incident"] or {})
    hazard_type = state.get("hazard_type", "general")

    query = " ".join(
        filter(
            None,
            [
                hazard_type.replace("_", " "),
                incident.sequence_of_events,
                *incident.immediate_causes,
                *incident.equipment_involved,
            ],
        )
    )
    clauses = await retrieve_regulatory_clauses(
        query, hazard_type=hazard_type, industry=incident.industry, k=CLAUSE_COUNT
    )
    families = violated_clause_families(clauses)

    return NodeResult(
        updates={"regulatory_clauses": [clause.model_dump(mode="json") for clause in clauses]},
        message=(
            f"Retrieved {len(clauses)} clauses implicating {len(families)} regulation families"
            if clauses
            else "No regulatory clauses matched. Check that the regulatory index is populated."
        ),
        data={"clause_count": len(clauses), "families": families},
    )
