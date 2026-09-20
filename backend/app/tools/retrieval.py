"""Retrieval tools: historical incidents and applicable regulatory clauses.

Clause text is always the retrieved passage. Nothing here asks a model to write
a regulation, so a citation that is not in the corpus cannot appear in output.
"""

from __future__ import annotations

import json
import logging
import re
from functools import lru_cache

from ..config import settings
from ..models import RegulatoryClause, RetrievedChunk, SimilarIncident
from ..rag.retriever import hybrid_search

logger = logging.getLogger(__name__)

MANIFEST_FILENAME = "corpus_manifest.json"
FALLBACK_CORPUS_SIZE = 1

# CFR part/section prefix -> the clause family used by the risk score weights.
_CLAUSE_FAMILIES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"1910\.147"), "lockout_tagout"),
    (re.compile(r"1910\.146"), "confined_space"),
    (re.compile(r"1910\.(21[0-9]|219)"), "machine_guarding"),
    (re.compile(r"(1926\.50[123]|1910\.2[89])"), "fall_protection"),
    (re.compile(r"1910\.13[2-8]"), "ppe_required"),
    (re.compile(r"1910\.1200"), "hazcom"),
    (re.compile(r"1910\.22"), "housekeeping"),
    (re.compile(r"1910\.(30[0-9]|33[0-9])"), "electrical"),
    (re.compile(r"1910\.25[23]"), "hot_work"),
    (re.compile(r"1910\.119"), "process_safety"),
    (re.compile(r"5\(a\)\(1\)|general duty", re.IGNORECASE), "general_duty_clause"),
)

# Confidence is derived from a clause's RANK, not from the reranker's raw score.
# FlashRank orders well but its magnitudes are not calibrated: it scores a
# verbatim-matching LOTO clause at 0.00003, which would make every clause look
# irrelevant. Rank is the part of its output that means something.
RANK_CONFIDENCE_TOP = 0.9
RANK_CONFIDENCE_DECAY = 0.12
RANK_CONFIDENCE_MIN = 0.1

# Above this a clause counts as a likely violation; below it, it is context.
# With k=6 that admits the top five and leaves the tail as background.
VIOLATION_CONFIDENCE_FLOOR = 0.35


def rank_confidence(rank: int) -> float:
    """Relevance for the rank-th result, best first."""
    return round(max(RANK_CONFIDENCE_TOP - RANK_CONFIDENCE_DECAY * rank, RANK_CONFIDENCE_MIN), 2)


@lru_cache(maxsize=1)
def corpus_size() -> int:
    """Number of historical incident documents indexed, from the ingest manifest."""
    manifest = settings.data_dir / MANIFEST_FILENAME
    if not manifest.exists():
        logger.warning("No %s; frequency scoring will use a corpus size of 1.", MANIFEST_FILENAME)
        return FALLBACK_CORPUS_SIZE
    return max(int(json.loads(manifest.read_text(encoding="utf-8")).get("document_count", 1)), 1)


def clause_family(regulation_name: str, section: str = "") -> str:
    """Map a citation to its weight family. Unrecognised citations fall back to general duty."""
    haystack = f"{regulation_name} {section}"
    for pattern, family in _CLAUSE_FAMILIES:
        if pattern.search(haystack):
            return family
    return "general_duty_clause"


async def hybrid_search_incidents(
    query: str, *, industry: str | None = None, k: int = 8
) -> list[SimilarIncident]:
    """Find historical incidents resembling this one.

    Runs BM25 and dense retrieval in parallel, merges with reciprocal rank
    fusion, reranks with a cross-encoder, and trims each passage to the
    sentences that earned the match.

    Industry narrows the search but never starves it. It is an inferred field
    and is often "unknown", so a corpus labelled mostly "chemical" would return
    nothing at all for a "manufacturing" report -- and no similar incidents
    means no frequency signal and no corroborated precursors. If filtering
    leaves too little, the search is repeated across every industry.
    """
    chunks: list[RetrievedChunk] = []
    if industry:
        chunks = await hybrid_search(
            settings.incidents_collection, query, k=k, metadata={"industry": industry}
        )
    if len(chunks) < max(k // 2, 1):
        chunks = await hybrid_search(settings.incidents_collection, query, k=k)
    return [_to_similar_incident(chunk, rank) for rank, chunk in enumerate(chunks)]


def _to_similar_incident(chunk: RetrievedChunk, rank: int) -> SimilarIncident:
    metadata = chunk.metadata
    return SimilarIncident(
        doc_id=chunk.chunk_id,
        title=metadata.get("title") or chunk.source_document,
        industry=metadata.get("industry", "unknown"),
        severity=metadata.get("severity", "UNKNOWN"),
        similarity_score=rank_confidence(rank),
        chunk_excerpt=chunk.text,
        source_document=chunk.source_document,
        incident_date=metadata.get("incident_date"),
        hazard_tags=[tag for tag in metadata.get("hazard_type", "").split(",") if tag],
    )


async def retrieve_regulatory_clauses(
    query: str, *, hazard_type: str | None = None, industry: str | None = None, k: int = 6
) -> list[RegulatoryClause]:
    """Retrieve the regulatory passages that apply to this incident.

    The returned clause_text is verbatim from the regulatory index; the
    confidence is the cross-encoder score, not a model's opinion.
    """
    metadata = {
        key: value for key, value in (("hazard_type", hazard_type), ("industry", industry)) if value
    }
    chunks = await hybrid_search(settings.regulatory_collection, query, k=k, metadata=metadata or None)
    return [_to_clause(chunk, rank) for rank, chunk in enumerate(chunks)]


def _to_clause(chunk: RetrievedChunk, rank: int) -> RegulatoryClause:
    regulation_name = chunk.metadata.get("regulation_name") or chunk.source_document
    confidence = rank_confidence(rank)
    family = clause_family(regulation_name, chunk.section)
    return RegulatoryClause(
        clause_id=chunk.chunk_id,
        regulation_name=regulation_name,
        section=chunk.section or chunk.metadata.get("section", ""),
        clause_text=chunk.text,
        violation_confidence=confidence,
        relevance_explanation=(
            f"Retrieved from {chunk.source_document} as a {family.replace('_', ' ')} requirement "
            f"matching the reported hazard."
        ),
    )


def violated_clause_families(clauses: list[RegulatoryClause]) -> list[str]:
    """De-duplicated weight families for clauses confident enough to count as violations."""
    families = {
        clause_family(clause.regulation_name, clause.section)
        for clause in clauses
        if clause.violation_confidence >= VIOLATION_CONFIDENCE_FLOOR
    }
    return sorted(families)
