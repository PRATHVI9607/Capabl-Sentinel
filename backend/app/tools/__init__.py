"""The ten SENTINEL tools.

Each tool is an ordinary typed Python function, so nodes and tests call it
directly with real arguments and real return types. `tool_registry()` wraps the
same functions as LangChain `StructuredTool`s, which derives each one's
argument schema from its signature and its description from its docstring.

That registry is what `GET /tools` serves: the agent's capabilities, their
parameters and their descriptions, generated from the code rather than written
out again beside it.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.tools import StructuredTool

from .actions import generate_corrective_actions
from .parsing import extract_hazard_entities, parse_incident_report
from .patterns import (
    build_causal_chain,
    detect_hazard_type,
    detect_precursor_patterns,
    known_precursor_count,
)
from .retrieval import (
    clause_family,
    corpus_size,
    hybrid_search_incidents,
    retrieve_regulatory_clauses,
    violated_clause_families,
)
from .scoring import classify_severity, compute_risk_score, score_incident
from .streaming import emit_stream_update

_ASYNC_TOOLS = (
    parse_incident_report,
    extract_hazard_entities,
    hybrid_search_incidents,
    retrieve_regulatory_clauses,
    classify_severity,
    generate_corrective_actions,
    emit_stream_update,
)
_SYNC_TOOLS = (
    compute_risk_score,
    detect_precursor_patterns,
    build_causal_chain,
)


def _as_tool(function) -> StructuredTool:
    return StructuredTool.from_function(
        func=function if function in _SYNC_TOOLS else None,
        coroutine=function if function in _ASYNC_TOOLS else None,
        name=function.__name__,
        description=(function.__doc__ or "").strip().split("\n\n")[0],
    )


@lru_cache(maxsize=1)
def tool_registry() -> dict[str, StructuredTool]:
    """Built on first use: schema inference is not free and nothing needs it at import."""
    return {function.__name__: _as_tool(function) for function in (*_ASYNC_TOOLS, *_SYNC_TOOLS)}


__all__ = [
    "tool_registry",
    "build_causal_chain",
    "classify_severity",
    "clause_family",
    "compute_risk_score",
    "corpus_size",
    "detect_hazard_type",
    "detect_precursor_patterns",
    "emit_stream_update",
    "extract_hazard_entities",
    "generate_corrective_actions",
    "hybrid_search_incidents",
    "known_precursor_count",
    "parse_incident_report",
    "retrieve_regulatory_clauses",
    "score_incident",
    "violated_clause_families",
]
