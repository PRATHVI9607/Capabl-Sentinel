"""Extract the structured incident from the report text."""

from __future__ import annotations

from ...tools import parse_incident_report
from ..state import SentinelState
from .base import NodeResult, node


@node("incident_parser", "Extracting incident structure...")
async def incident_parser(state: SentinelState) -> NodeResult:
    incident = await parse_incident_report(state["raw_text"])

    warnings = list(state.get("warnings", []))
    if incident.extraction_confidence < 0.5:
        warnings.append(
            f"Only {incident.extraction_confidence:.0%} of the incident schema could be filled "
            "from this document."
        )

    return NodeResult(
        updates={"incident": incident.model_dump(mode="json"), "warnings": warnings},
        message=(
            f"Parsed {incident.industry or 'unspecified industry'} incident, "
            f"severity {incident.severity_indicator.value}"
        ),
        data={
            "industry": incident.industry,
            "severity": incident.severity_indicator.value,
            "confidence": incident.extraction_confidence,
        },
    )
