"""Find historical matches, then the precursor patterns they corroborate."""

from __future__ import annotations

from ...models import IncidentReport
from ...tools import build_causal_chain, detect_precursor_patterns, hybrid_search_incidents
from ..state import SentinelState
from .base import NodeResult, node

# Enough historical context to corroborate a pattern without drowning the UI.
SIMILAR_INCIDENT_COUNT = 8


def _search_query(incident: IncidentReport, raw_text: str) -> str:
    """Prefer the parsed narrative; fall back to the opening of the raw report."""
    parts = [incident.sequence_of_events, *incident.immediate_causes, *incident.equipment_involved]
    query = " ".join(part for part in parts if part).strip()
    return query or raw_text[:1000]


@node("pattern_detector", "Searching historical incidents for precursor patterns...")
async def pattern_detector(state: SentinelState) -> NodeResult:
    incident = IncidentReport.model_validate(state["incident"] or {})
    similar = await hybrid_search_incidents(
        _search_query(incident, state["raw_text"]),
        industry=incident.industry,
        k=SIMILAR_INCIDENT_COUNT,
    )
    patterns = detect_precursor_patterns(state["raw_text"], similar, hazard_type=state.get("hazard_type"))
    chain = build_causal_chain(
        incident.equipment_involved,
        [entity["text"] for entity in state.get("entities", []) if entity["entity_type"] == "HAZARD"],
        incident.immediate_causes + incident.root_causes,
    )

    return NodeResult(
        updates={
            "similar_incidents": [item.model_dump(mode="json") for item in similar],
            "precursor_patterns": [pattern.model_dump(mode="json") for pattern in patterns],
            "causal_chain": [event.model_dump(mode="json") for event in chain],
        },
        message=(
            f"Found {len(patterns)} precursor patterns across {len(similar)} similar historical incidents"
        ),
        data={"pattern_count": len(patterns), "similar_count": len(similar)},
    )
