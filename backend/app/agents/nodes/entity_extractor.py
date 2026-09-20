"""Pull hazard entities out of the text and settle on a hazard family."""

from __future__ import annotations

from ...models import IncidentReport
from ...tools import detect_hazard_type, extract_hazard_entities
from ..state import SentinelState
from .base import NodeResult, node


@node("entity_extractor", "Extracting hazard entities...")
async def entity_extractor(state: SentinelState) -> NodeResult:
    entities = await extract_hazard_entities(state["raw_text"])
    incident = IncidentReport.model_validate(state["incident"] or {})

    # Hazard family comes from the narrative plus the causes the parser found, which
    # name the hazard more directly than the surrounding prose does.
    hazard_text = " ".join(
        [state["raw_text"], incident.sequence_of_events, *incident.immediate_causes, *incident.root_causes]
    )
    hazard_type = detect_hazard_type(hazard_text)

    return NodeResult(
        updates={
            "entities": [entity.model_dump(mode="json") for entity in entities],
            "hazard_type": hazard_type,
        },
        message=f"Found {len(entities)} entities; hazard family: {hazard_type.replace('_', ' ')}",
        data={"entity_count": len(entities), "hazard_type": hazard_type},
    )
