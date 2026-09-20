"""Priority synthesis path, taken when the risk score reaches 8.0 or above."""

from __future__ import annotations

from ..state import SentinelState
from .base import NodeResult, node
from .synthesis import synthesize


@node("priority_alert_synthesizer", "CRITICAL risk - escalating alert synthesis...")
async def priority_alert_synthesizer(state: SentinelState) -> NodeResult:
    alert, actions, report = await synthesize(state, priority=True)
    immediate = [action for action in actions if action.urgency.value == "IMMEDIATE"]
    return NodeResult(
        updates={
            "alerts": [alert.model_dump(mode="json")],
            "corrective_actions": [action.model_dump(mode="json") for action in actions],
            "analysis_report": report.model_dump(mode="json"),
        },
        message=f"CRITICAL alert raised with {len(immediate)} immediate actions",
        data={"severity": alert.severity.value, "immediate_actions": len(immediate)},
    )
