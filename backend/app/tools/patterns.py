"""Precursor detection and causal chain traversal.

A precursor is a condition that was present before this incident and has been
present before others like it. Detection is evidence-based: a pattern is only
reported with the count of historical incidents that show it too.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from ..config import settings
from ..knowledge_graph import graph as kg
from ..knowledge_graph import serializer
from ..models import CausalEvent, PrecursorPattern, SimilarIncident

GENERAL_HAZARD = "general"


@dataclass(frozen=True)
class PrecursorDefinition:
    hazard_type: str
    pattern_name: str
    description: str
    keywords: tuple[str, ...]

    def matches(self, lowered_text: str) -> bool:
        return any(keyword in lowered_text for keyword in self.keywords)


@lru_cache(maxsize=1)
def taxonomy() -> dict[str, tuple[PrecursorDefinition, ...]]:
    """Load data/precursors.json once, as immutable definitions."""
    raw = json.loads((settings.data_dir / "precursors.json").read_text(encoding="utf-8"))
    return {
        hazard_type: tuple(
            PrecursorDefinition(
                hazard_type=hazard_type,
                pattern_name=entry["pattern_name"],
                description=entry["description"],
                keywords=tuple(entry["keywords"]),
            )
            for entry in entries
        )
        for hazard_type, entries in raw.items()
        if not hazard_type.startswith("_")
    }


def detect_hazard_type(text: str) -> str:
    """Pick the hazard family whose precursor keywords the text hits most."""
    lowered = text.lower()
    scores = {
        hazard_type: sum(definition.matches(lowered) for definition in definitions)
        for hazard_type, definitions in taxonomy().items()
        if hazard_type != GENERAL_HAZARD
    }
    best = max(scores, key=lambda key: scores[key], default=GENERAL_HAZARD)
    return best if scores.get(best, 0) > 0 else GENERAL_HAZARD


def known_precursor_count(hazard_type: str) -> int:
    """Denominator of the precursor-density component of the risk score."""
    definitions = taxonomy()
    return len(definitions.get(hazard_type, ())) + len(definitions.get(GENERAL_HAZARD, ()))


def detect_precursor_patterns(
    text: str,
    similar_incidents: list[SimilarIncident],
    *,
    hazard_type: str | None = None,
) -> list[PrecursorPattern]:
    """Precursor patterns present in this report, ranked by historical corroboration.

    Every pattern found in the report is returned, carrying the number of
    retrieved historical incidents that show it too. Nothing is hidden behind a
    corroboration threshold: only about eight compressed excerpts are retrieved,
    so any meaningful cutoff silently discards real findings. `evidence_count`
    is the honest signal, and 0 is a legitimate value the UI renders as "not
    corroborated in the corpus".

    Confidence rises with corroboration and is capped at 0.95: a keyword match
    is strong evidence, never proof.
    """
    lowered = text.lower()
    hazard_type = hazard_type or detect_hazard_type(text)
    definitions = taxonomy().get(hazard_type, ()) + taxonomy().get(GENERAL_HAZARD, ())
    historical = [incident.chunk_excerpt.lower() for incident in similar_incidents]

    patterns: list[PrecursorPattern] = []
    for definition in definitions:
        if not definition.matches(lowered):
            continue
        evidence = sum(definition.matches(excerpt) for excerpt in historical)
        patterns.append(
            PrecursorPattern(
                pattern_name=definition.pattern_name,
                description=definition.description,
                confidence=min(0.55 + 0.1 * evidence, 0.95),
                evidence_count=evidence,
                hazard_types=[definition.hazard_type],
            )
        )
    return sorted(patterns, key=lambda pattern: pattern.evidence_count, reverse=True)


def build_causal_chain(equipment: list[str], hazards: list[str], causes: list[str]) -> list[CausalEvent]:
    """Walk the corpus knowledge graph outward from this incident's entities.

    Falls back to the incident's own causes when the graph has nothing to add, so
    the timeline is never empty for a report that named its causes.
    """
    graph = serializer.load()
    events: list[CausalEvent] = []
    seen: set[str] = set()

    for label in causes:
        key = label.strip().lower()
        if key and key not in seen:
            seen.add(key)
            events.append(
                CausalEvent(order=len(events), label=label, node_type="cause", relation=kg.CAUSED_BY)
            )

    for node_type, labels in (("equipment", equipment), ("hazard", hazards)):
        for label in labels:
            node = kg.node_key(node_type, label)
            for step in kg.find_precursor_chain(graph, node):
                key = step.label.strip().lower()
                if key in seen:
                    continue
                seen.add(key)
                events.append(
                    CausalEvent(
                        order=len(events),
                        label=step.label,
                        node_type=step.node_type,
                        relation=step.relation,
                    )
                )
    return events
