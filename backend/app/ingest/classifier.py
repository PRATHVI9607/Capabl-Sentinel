"""Decide what kind of document was uploaded.

Keyword scoring answers the clear-cut majority for free; the LLM is only asked
about documents that score ambiguously.
"""

from __future__ import annotations

import logging
from typing import Literal

from pydantic import BaseModel, Field

from ..llm import LLMUnavailable, complete_structured

logger = logging.getLogger(__name__)

DocumentType = Literal["incident", "regulatory", "unknown"]

_INCIDENT_TERMS = (
    "incident",
    "accident",
    "injury",
    "fatality",
    "employee was",
    "investigation",
    "root cause",
    "near miss",
    "struck by",
    "witness",
    "occurred on",
)
_REGULATORY_TERMS = (
    "29 cfr",
    "shall be",
    "the employer shall",
    "subpart",
    "standard number",
    "this section applies",
    "regulation",
    "compliance with paragraph",
)
_DECISIVE_MARGIN = 2


class _Verdict(BaseModel):
    document_type: DocumentType = Field(description="incident | regulatory | unknown")


def score_keywords(text: str) -> tuple[int, int]:
    lowered = text[:20_000].lower()
    return (
        sum(term in lowered for term in _INCIDENT_TERMS),
        sum(term in lowered for term in _REGULATORY_TERMS),
    )


async def classify(text: str) -> DocumentType:
    incident_hits, regulatory_hits = score_keywords(text)
    if abs(incident_hits - regulatory_hits) >= _DECISIVE_MARGIN:
        return "incident" if incident_hits > regulatory_hits else "regulatory"

    try:
        verdict = await complete_structured(
            [
                (
                    "system",
                    "Classify the document as 'incident' (a report of a specific workplace "
                    "event), 'regulatory' (a standard, code, or statute), or 'unknown'.",
                ),
                ("human", text[:4000]),
            ],
            _Verdict,
            fast=True,
        )
    except LLMUnavailable:
        logger.info("No LLM available for classification; defaulting to keyword winner.")
        return "incident" if incident_hits >= regulatory_hits else "regulatory"
    return verdict.document_type
