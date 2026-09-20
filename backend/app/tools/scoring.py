"""Severity classification and the risk score.

`compute_risk_score` is pure Python and fully deterministic: the same inputs
always produce the same number, and every component is reported with the weight
that produced it so the total can be checked by hand.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable

from pydantic import BaseModel, Field

from ..llm import LLMUnavailable, complete_structured
from ..models import IncidentReport, RiskComponent, RiskScore, SeverityTier

logger = logging.getLogger(__name__)

# Relative seriousness of each regulation family. General duty is weighted highest
# because it is cited when a recognised hazard was left uncontrolled at all.
CLAUSE_WEIGHT_MAP: dict[str, float] = {
    "general_duty_clause": 2.0,
    "confined_space": 1.9,
    "lockout_tagout": 1.8,
    "machine_guarding": 1.7,
    "electrical": 1.7,
    "fall_protection": 1.6,
    "process_safety": 1.6,
    "hot_work": 1.5,
    "ppe_required": 1.5,
    "hazcom": 1.4,
    "housekeeping": 1.0,
}
DEFAULT_CLAUSE_WEIGHT = 1.0

SEVERITY_TO_SCORE: dict[SeverityTier, float] = {
    SeverityTier.CRITICAL: 9.5,
    SeverityTier.HIGH: 7.5,
    SeverityTier.MEDIUM: 5.0,
    SeverityTier.LOW: 2.5,
    SeverityTier.UNKNOWN: 4.0,
}

WEIGHTS = {"severity": 0.30, "frequency": 0.25, "regulatory": 0.25, "precursor": 0.20}

# Corpus share at which the frequency component saturates at 10/10. Both sides
# of the ratio are document counts. 25.0 means "40% of the corpus resembles this
# incident" is maximal, which keeps the component spanning a useful range
# instead of pinning at the first match.
FREQUENCY_SCALE = 25.0
REGULATORY_SCALE = 1.2

TIER_THRESHOLDS = ((8.0, SeverityTier.CRITICAL), (6.0, SeverityTier.HIGH), (4.0, SeverityTier.MEDIUM))

_CRITICAL_TERMS = ("fatality", "fatal", "died", "death", "killed", "deceased", "pronounced dead")
_HIGH_TERMS = (
    "amputation",
    "amputated",
    "hospitalized",
    "hospitalised",
    "catastrophic",
    "critical condition",
    "permanent disability",
    "loss of an eye",
    "third-degree burn",
    "life-threatening",
    "airlifted",
)
_MEDIUM_TERMS = ("injury", "injured", "laceration", "fracture", "lost time", "medical treatment", "burn")
_LOW_TERMS = ("near miss", "near-miss", "no injuries", "no injury", "property damage only", "close call")

_MULTI_INJURY_THRESHOLD = 3

# "No fatalities occurred" contains "fatal", so a plain substring search reads a
# report's good news as its worst outcome. These are checked first and strip the
# phrase before the positive terms are matched.
_OUTCOME = r"(?:fatalit\w*|fatal\w*|death\w*|died|injur\w*|casualt\w*|harm)"
_NEGATED = re.compile(
    r"\b(?:no|zero|without|nor)\s+" r"(?:reported\s+|known\s+|serious\s+|other\s+)?"
    # The trailing group catches lists: "no injuries or fatalities".
    rf"{_OUTCOME}(?:\s*(?:,|or|and|nor)\s*{_OUTCOME})*",
    re.IGNORECASE,
)


class _SeverityVerdict(BaseModel):
    tier: SeverityTier = Field(description="CRITICAL, HIGH, MEDIUM or LOW")


def tier_for(total: float) -> SeverityTier:
    for threshold, tier in TIER_THRESHOLDS:
        if total >= threshold:
            return tier
    return SeverityTier.LOW


def _contains(text: str, terms: Iterable[str]) -> bool:
    return any(term in text for term in terms)


def classify_severity_by_rules(
    text: str, *, injury_count: int = 0, fatality_count: int = 0
) -> SeverityTier | None:
    """Keyword and count rules. Returns None only when nothing is decisive.

    Negated outcomes are stripped before the escalating checks, so "no
    fatalities occurred" no longer reads as a death. They are kept for the LOW
    check, where stating that nobody was hurt is itself the signal.
    """
    lowered = re.sub(r"\s+", " ", text.lower())
    stated = _NEGATED.sub(" ", lowered)

    if fatality_count > 0 or _contains(stated, _CRITICAL_TERMS):
        return SeverityTier.CRITICAL
    if injury_count >= _MULTI_INJURY_THRESHOLD or _contains(stated, _HIGH_TERMS):
        return SeverityTier.HIGH
    if injury_count > 0 or _contains(stated, _MEDIUM_TERMS):
        return SeverityTier.MEDIUM
    if _contains(lowered, _LOW_TERMS) or _NEGATED.search(lowered):
        return SeverityTier.LOW
    return None


async def classify_severity(text: str, *, injury_count: int = 0, fatality_count: int = 0) -> SeverityTier:
    """Rules first; the LLM is only asked about reports no rule matched."""
    verdict = classify_severity_by_rules(text, injury_count=injury_count, fatality_count=fatality_count)
    if verdict is not None:
        return verdict
    try:
        result = await complete_structured(
            [
                (
                    "system",
                    "Assign a severity tier to this workplace safety report. CRITICAL: a death. "
                    "HIGH: amputation, hospitalisation or permanent harm. MEDIUM: a treatable "
                    "injury. LOW: a near miss or property damage only.",
                ),
                ("human", text[:4000]),
            ],
            _SeverityVerdict,
            fast=True,
        )
    except LLMUnavailable:
        logger.info("No LLM available for severity refinement; reporting UNKNOWN.")
        return SeverityTier.UNKNOWN
    return result.tier


def compute_risk_score(
    *,
    severity: SeverityTier,
    similar_count: int,
    corpus_size: int,
    violated_clauses: list[str],
    detected_precursors: int,
    known_precursors: int,
) -> RiskScore:
    """Weighted four-component risk score in 0-10. No LLM involved.

    R = 0.30*severity + 0.25*frequency + 0.25*regulatory + 0.20*precursor_density
    """
    severity_score = SEVERITY_TO_SCORE.get(severity, SEVERITY_TO_SCORE[SeverityTier.UNKNOWN])
    frequency_score = min(similar_count / max(corpus_size, 1) * FREQUENCY_SCALE, 10.0)
    regulatory_score = min(
        sum(CLAUSE_WEIGHT_MAP.get(clause, DEFAULT_CLAUSE_WEIGHT) for clause in violated_clauses)
        * REGULATORY_SCALE,
        10.0,
    )
    precursor_score = min(detected_precursors / max(known_precursors, 1) * 10.0, 10.0)

    # Rounded before weighting so the four numbers the UI shows add up to the
    # total the UI shows. An explainable score that does not reconcile by hand
    # is not explainable.
    severity_score = round(severity_score, 2)
    frequency_score = round(frequency_score, 2)
    regulatory_score = round(regulatory_score, 2)
    precursor_score = round(precursor_score, 2)

    total = round(
        WEIGHTS["severity"] * severity_score
        + WEIGHTS["frequency"] * frequency_score
        + WEIGHTS["regulatory"] * regulatory_score
        + WEIGHTS["precursor"] * precursor_score,
        2,
    )
    tier = tier_for(total)
    components = [
        RiskComponent(
            name="Severity",
            score=severity_score,
            weight=WEIGHTS["severity"],
            explanation=f"Classified {severity.value} from the report outcome.",
        ),
        RiskComponent(
            name="Frequency",
            score=frequency_score,
            weight=WEIGHTS["frequency"],
            explanation=f"{similar_count} of {corpus_size} indexed historical documents matched.",
        ),
        RiskComponent(
            name="Regulatory",
            score=regulatory_score,
            weight=WEIGHTS["regulatory"],
            explanation=f"{len(violated_clauses)} regulation families implicated: "
            f"{', '.join(violated_clauses) or 'none'}.",
        ),
        RiskComponent(
            name="Precursor Density",
            score=precursor_score,
            weight=WEIGHTS["precursor"],
            explanation=(
                f"{detected_precursors} of {known_precursors} known precursors "
                "for this hazard type are present."
            ),
        ),
    ]
    return RiskScore(
        total=total,
        tier=tier,
        components=components,
        explanation=(
            f"Risk {total}/10 ({tier.value}). "
            + " ".join(f"{c.name} {c.score}x{c.weight}." for c in components)
        ),
    )


def score_incident(
    incident: IncidentReport,
    *,
    similar_count: int,
    corpus_size: int,
    violated_clauses: list[str],
    detected_precursors: int,
    known_precursors: int,
) -> RiskScore:
    """Convenience wrapper so callers pass the parsed report rather than loose fields."""
    return compute_risk_score(
        severity=incident.severity_indicator,
        similar_count=similar_count,
        corpus_size=corpus_size,
        violated_clauses=violated_clauses,
        detected_precursors=detected_precursors,
        known_precursors=known_precursors,
    )
