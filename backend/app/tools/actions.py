"""Corrective action generation.

Templates first: a known hazard type has a reviewed set of controls with the
right regulation pointers. The LLM is only used for hazard types the table does
not cover, and its output is clearly sourced as generated.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache

from pydantic import BaseModel, Field

from ..config import settings
from ..llm import LLMUnavailable, complete_structured
from ..models import CorrAction, PrecursorPattern, RegulatoryClause, Urgency

logger = logging.getLogger(__name__)

_URGENCY_ORDER = {Urgency.IMMEDIATE: 0, Urgency.SHORT_TERM: 1, Urgency.LONG_TERM: 2}
GENERAL_HAZARD = "general"
MAX_GENERATED_ACTIONS = 4


class _GeneratedActions(BaseModel):
    actions: list[CorrAction] = Field(default_factory=list)


@lru_cache(maxsize=1)
def _templates() -> dict[str, list[dict]]:
    raw = json.loads((settings.data_dir / "actions.json").read_text(encoding="utf-8"))
    return {key: value for key, value in raw.items() if not key.startswith("_")}


def sort_by_urgency(actions: list[CorrAction]) -> list[CorrAction]:
    return sorted(actions, key=lambda action: _URGENCY_ORDER[action.urgency])


async def generate_corrective_actions(
    hazard_type: str,
    *,
    precursors: list[PrecursorPattern] | None = None,
    clauses: list[RegulatoryClause] | None = None,
    summary: str = "",
) -> list[CorrAction]:
    """Controls for this hazard type, most urgent first."""
    templates = _templates()
    entries = templates.get(hazard_type) or []
    if not entries:
        entries = await _generate(hazard_type, summary, precursors or [], clauses or [])
    entries = entries + templates.get(GENERAL_HAZARD, [])

    actions = [CorrAction.model_validate(entry) for entry in entries]
    return sort_by_urgency(_deduplicate(actions))


def _deduplicate(actions: list[CorrAction]) -> list[CorrAction]:
    seen: set[str] = set()
    unique: list[CorrAction] = []
    for action in actions:
        key = action.action.strip().lower()
        if key not in seen:
            seen.add(key)
            unique.append(action)
    return unique


async def _generate(
    hazard_type: str,
    summary: str,
    precursors: list[PrecursorPattern],
    clauses: list[RegulatoryClause],
) -> list[dict]:
    """LLM fallback for hazard types with no template entry."""
    try:
        generated = await complete_structured(
            [
                (
                    "system",
                    "Propose corrective actions for a workplace safety incident. Each action is "
                    "one concrete, verifiable step. Use urgency IMMEDIATE, SHORT_TERM or "
                    "LONG_TERM. Set regulation_reference only to a standard listed in the "
                    "provided clauses; otherwise leave it null. Return at most "
                    f"{MAX_GENERATED_ACTIONS} actions.",
                ),
                (
                    "human",
                    f"Hazard type: {hazard_type}\n"
                    f"Incident: {summary[:2000]}\n"
                    f"Precursors: {', '.join(p.pattern_name for p in precursors) or 'none detected'}\n"
                    f"Clauses: {', '.join(c.regulation_name for c in clauses) or 'none retrieved'}",
                ),
            ],
            _GeneratedActions,
        )
    except LLMUnavailable:
        logger.info("No LLM available for action generation; using general controls only.")
        return []
    return [action.model_dump() for action in generated.actions[:MAX_GENERATED_ACTIONS]]
