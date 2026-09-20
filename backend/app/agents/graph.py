"""The SENTINEL state machine.

Linear through extraction and scoring, then one conditional edge that picks the
synthesis path -- or diverts to the error handler if any earlier node failed.
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, StateGraph

from .nodes import (
    alert_synthesizer,
    document_router,
    entity_extractor,
    error_handler,
    incident_parser,
    pattern_detector,
    priority_alert_synthesizer,
    regulatory_auditor,
    risk_scorer,
)
from .state import SentinelState

CRITICAL_THRESHOLD = 8.0

# The longest legitimate path is seven nodes; the headroom exists so that a
# future cycle is caught rather than a normal run being cut short. LangGraph
# raises GraphRecursionError past this, which the pipeline turns into a failure.
RECURSION_LIMIT = 15
GRAPH_CONFIG = {"recursion_limit": RECURSION_LIMIT}

_PIPELINE = (
    ("document_router", document_router),
    ("incident_parser", incident_parser),
    ("entity_extractor", entity_extractor),
    ("pattern_detector", pattern_detector),
    ("regulatory_auditor", regulatory_auditor),
    ("risk_scorer", risk_scorer),
)


def route_after_scoring(state: SentinelState) -> str:
    """CRITICAL findings get the priority synthesis path; failures get the handler."""
    if state.get("error"):
        return "error"
    total = (state.get("risk_score") or {}).get("total", 0.0)
    return "priority" if total >= CRITICAL_THRESHOLD else "standard"


def build_graph():
    graph = StateGraph(SentinelState)
    for name, function in _PIPELINE:
        graph.add_node(name, function)
    graph.add_node("alert_synthesizer", alert_synthesizer)
    graph.add_node("priority_alert_synthesizer", priority_alert_synthesizer)
    graph.add_node("error_handler", error_handler)

    graph.set_entry_point(_PIPELINE[0][0])
    for (name, _), (next_name, _) in zip(_PIPELINE, _PIPELINE[1:], strict=False):
        graph.add_edge(name, next_name)

    graph.add_conditional_edges(
        "risk_scorer",
        route_after_scoring,
        {
            "priority": "priority_alert_synthesizer",
            "standard": "alert_synthesizer",
            "error": "error_handler",
        },
    )
    graph.add_edge("alert_synthesizer", END)
    graph.add_edge("priority_alert_synthesizer", END)
    graph.add_edge("error_handler", END)
    return graph.compile()


@lru_cache(maxsize=1)
def sentinel_graph():
    """Compiled once per process; compilation is not free and the graph is static."""
    return build_graph()


async def run_graph(state: SentinelState) -> SentinelState:
    """Execute the compiled graph under the recursion limit."""
    return await sentinel_graph().ainvoke(state, config=GRAPH_CONFIG)
