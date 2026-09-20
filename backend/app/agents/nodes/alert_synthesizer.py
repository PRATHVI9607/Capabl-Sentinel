"""Standard synthesis path, taken when the risk score is below 8.0."""

from __future__ import annotations

from ..state import SentinelState
from .base import NodeResult, node
from .synthesis import synthesize


@node("alert_synthesizer", "Synthesizing alert and corrective actions...")
async def alert_synthesizer(state: SentinelState) -> NodeResult:
    alert, actions, report = await synthesize(state, priority=False)
    return NodeResult(
        updates={
            "alerts": [alert.model_dump(mode="json")],
            "corrective_actions": [action.model_dump(mode="json") for action in actions],
            "analysis_report": report.model_dump(mode="json"),
        },
        message=f"{alert.severity.value} alert raised with {len(actions)} corrective actions",
        data={"severity": alert.severity.value, "action_count": len(actions)},
    )
