"""Turn raw report text into an IncidentReport and a list of hazard entities."""

from __future__ import annotations

import asyncio
import json
import logging
from functools import lru_cache

from pydantic import BaseModel, Field

from ..config import settings
from ..llm import LLMUnavailable, complete_structured
from ..models import EntityType, HazardEntity, IncidentReport, SeverityTier
from .scoring import classify_severity_by_rules

logger = logging.getLogger(__name__)

# Enough context for the narrative without paying for the whole appendix.
_PARSE_CHAR_BUDGET = 12_000

_EXTRACTION_SYSTEM_PROMPT = (
    "You extract structured facts from workplace safety incident reports. "
    "Use only what the document states. Leave a field empty rather than inferring, "
    "guessing, or filling it with a plausible value. Quote equipment and causes in "
    "the document's own words."
)

# spaCy exposes no per-entity probability, so these are fixed priors. A
# dictionary rule that fired is near-certain; a statistical guess is not; an
# entity the model proposed sits between the two.
_RULE_CONFIDENCE = 0.9
_LLM_CONFIDENCE = 0.75
_MODEL_CONFIDENCE = 0.6
_LLM_VERIFY_THRESHOLD = 0.7
_MAX_ENTITIES = 40

# Only relevant when a statistical model is configured; the entity ruler covers
# equipment far better than a general-purpose NER does on this vocabulary.
_SPACY_LABEL_MAP = {"PRODUCT": EntityType.EQUIPMENT, "FAC": EntityType.EQUIPMENT}


class _Verification(BaseModel):
    keep: list[str] = Field(
        default_factory=list, description="entity texts that are genuine safety entities"
    )


class _DiscoveredEntity(BaseModel):
    text: str = Field(description="copied verbatim from the report")
    entity_type: EntityType


class _EntityDiscovery(BaseModel):
    entities: list[_DiscoveredEntity] = Field(default_factory=list)


class _ParsedIncident(BaseModel):
    """LLM-facing schema. Deliberately flat and free of defaults the model can lean on."""

    incident_date: str | None = Field(default=None, description="as written in the document")
    location: str | None = None
    industry: str | None = Field(default=None, description="e.g. construction, chemical, manufacturing")
    equipment_involved: list[str] = Field(default_factory=list)
    sequence_of_events: str = Field(default="", description="what happened, in order, in 2-5 sentences")
    immediate_causes: list[str] = Field(default_factory=list)
    root_causes: list[str] = Field(default_factory=list)
    injury_count: int = 0
    fatality_count: int = 0


async def parse_incident_report(text: str) -> IncidentReport:
    """Extract the structured incident. Degrades to a text-only report if no LLM is configured."""
    excerpt = text[:_PARSE_CHAR_BUDGET]
    try:
        parsed = await complete_structured(
            [("system", _EXTRACTION_SYSTEM_PROMPT), ("human", excerpt)], _ParsedIncident
        )
    except LLMUnavailable:
        logger.warning("No LLM configured; returning a rules-only incident report.")
        return IncidentReport(
            sequence_of_events=excerpt[:1000],
            severity_indicator=classify_severity_by_rules(text) or SeverityTier.UNKNOWN,
            raw_text_length=len(text),
            extraction_confidence=0.2,
        )

    severity = classify_severity_by_rules(
        text, injury_count=parsed.injury_count, fatality_count=parsed.fatality_count
    )
    return IncidentReport(
        **parsed.model_dump(),
        severity_indicator=severity or SeverityTier.UNKNOWN,
        raw_text_length=len(text),
        extraction_confidence=_extraction_confidence(parsed, text),
    )


def _extraction_confidence(parsed: _ParsedIncident, text: str) -> float:
    """How much of the schema the document actually supported."""
    filled = sum(
        bool(value)
        for value in (
            parsed.incident_date,
            parsed.location,
            parsed.industry,
            parsed.equipment_involved,
            parsed.sequence_of_events,
            parsed.immediate_causes,
        )
    )
    short_document_penalty = 0.5 if len(text.split()) < settings.low_confidence_word_count else 1.0
    return round(filled / 6 * short_document_penalty, 2)


BLANK_PIPELINE = "blank"


@lru_cache(maxsize=1)
def _nlp():
    """Tokeniser plus the safety entity ruler. None if spaCy is not installed.

    The default is a blank English pipeline. Measured on real incident text, the
    `en_core_web_sm` statistical NER contributes nothing this domain can use --
    its extra entities are dates and cardinals, while every hazard, chemical,
    piece of equipment, unsafe condition and unsafe act comes from the ruler.
    Skipping it removes a 12MB model, a build step and most of the load time.

    Set SPACY_MODEL to a real pipeline name to layer statistical NER back on;
    its entities arrive at lower confidence and are sent for LLM verification.
    """
    try:
        import spacy
    except ImportError:
        logger.warning("spaCy not installed; entity extraction will rely on the LLM alone.")
        return None

    if settings.spacy_model == BLANK_PIPELINE:
        nlp = spacy.blank("en")
        ruler = nlp.add_pipe("entity_ruler")
    else:
        try:
            nlp = spacy.load(settings.spacy_model, exclude=["lemmatizer", "textcat"])
        except OSError:
            logger.warning(
                "spaCy model %s is not installed; falling back to a blank pipeline.",
                settings.spacy_model,
            )
            nlp = spacy.blank("en")
        ruler = nlp.add_pipe(
            "entity_ruler",
            before="ner" if "ner" in nlp.pipe_names else None,
            config={"overwrite_ents": True},
        )

    ruler.add_patterns(_patterns())
    return nlp


@lru_cache(maxsize=1)
def _patterns() -> list[dict]:
    return json.loads((settings.data_dir / "entity_patterns.json").read_text(encoding="utf-8"))


def spacy_entities(text: str) -> list[HazardEntity]:
    """Dictionary-rule and statistical NER entities. Sync; called from a thread."""
    nlp = _nlp()
    if nlp is None:
        return []

    seen: dict[str, HazardEntity] = {}
    for entity in nlp(text[:_PARSE_CHAR_BUDGET]).ents:
        entity_type = _entity_type(entity.label_)
        if entity_type is None:
            continue
        key = entity.text.strip().lower()
        if not key or key in seen:
            continue
        # A ruler pattern carries our own label; anything else came from the statistical NER.
        from_rule = entity.label_ in EntityType.__members__
        seen[key] = HazardEntity(
            text=entity.text.strip(),
            entity_type=entity_type,
            confidence=_RULE_CONFIDENCE if from_rule else _MODEL_CONFIDENCE,
            source="spacy",
        )
    return list(seen.values())[:_MAX_ENTITIES]


def _entity_type(label: str) -> EntityType | None:
    if label in EntityType.__members__:
        return EntityType[label]
    return _SPACY_LABEL_MAP.get(label)


async def extract_hazard_entities(text: str) -> list[HazardEntity]:
    """Dictionary matches from spaCy, then the LLM for what the dictionary cannot know.

    The entity ruler is a closed vocabulary: precise on what it covers, blind to
    everything else. So the model is asked to propose entities that are *not*
    already found, rather than to re-confirm ones that are -- recall is the real
    gap, and a second opinion on a verbatim dictionary hit buys nothing. Every
    entity carries its `source`, so the UI can show which is which.
    """
    entities = await asyncio.to_thread(spacy_entities, text)
    entities = await _verify_uncertain(text, entities)
    if len(entities) >= _MAX_ENTITIES:
        return entities
    return entities + await _discover_missing(text, entities)


async def _verify_uncertain(text: str, entities: list[HazardEntity]) -> list[HazardEntity]:
    """Adjudicate statistical-NER guesses. A no-op under the default blank pipeline."""
    uncertain = [entity for entity in entities if entity.confidence < _LLM_VERIFY_THRESHOLD]
    if not uncertain:
        return entities

    try:
        verification = await complete_structured(
            [
                (
                    "system",
                    "Some of these candidate entities are not real safety entities. Return only "
                    "the ones that name a hazard, a piece of equipment, a chemical, an unsafe "
                    "condition, or an unsafe act in this report. Copy the texts exactly.",
                ),
                (
                    "human",
                    "Report:\n"
                    + text[:3000]
                    + "\n\nCandidates:\n"
                    + "\n".join(f"- {entity.text}" for entity in uncertain),
                ),
            ],
            _Verification,
            fast=True,
        )
    except LLMUnavailable:
        return entities

    kept = {item.strip().lower() for item in verification.keep}
    return [
        entity
        for entity in entities
        if entity.confidence >= _LLM_VERIFY_THRESHOLD or entity.text.lower() in kept
    ]


async def _discover_missing(text: str, found: list[HazardEntity]) -> list[HazardEntity]:
    """Ask for safety entities the pattern dictionary does not cover."""
    known = {entity.text.strip().lower() for entity in found}
    try:
        discovery = await complete_structured(
            [
                (
                    "system",
                    "List safety-relevant entities in this incident report: hazards, equipment, "
                    "chemicals, unsafe conditions and unsafe acts. Copy each one verbatim from "
                    "the report. Do not invent entities and do not repeat the ones already listed "
                    "as found.",
                ),
                (
                    "human",
                    "Report:\n"
                    + text[:4000]
                    + "\n\nAlready found:\n"
                    + ("\n".join(f"- {entity.text}" for entity in found) or "- (none)"),
                ),
            ],
            _EntityDiscovery,
            fast=True,
        )
    except LLMUnavailable:
        return []

    discovered: list[HazardEntity] = []
    budget = _MAX_ENTITIES - len(found)
    for entity in discovery.entities:
        label = entity.text.strip()
        # Guard against the model returning text that is not in the document.
        if not label or label.lower() in known or label.lower() not in text.lower():
            continue
        known.add(label.lower())
        discovered.append(
            HazardEntity(
                text=label,
                entity_type=entity.entity_type,
                confidence=_LLM_CONFIDENCE,
                source="llm",
            )
        )
        if len(discovered) >= budget:
            break
    return discovered
