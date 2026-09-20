"""NetworkX causal graph over the historical corpus.

Nodes are incidents, equipment, hazards and causes. Traversing outward from an
incident produces the causal chain the UI renders as a timeline.
"""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

INVOLVED = "INVOLVED"
CAUSED_BY = "CAUSED_BY"
PRECEDED_BY = "PRECEDED_BY"

# Only these relations form a causal chain; INVOLVED edges are context, not causation.
_CAUSAL_RELATIONS = (CAUSED_BY, PRECEDED_BY)
MAX_CHAIN_DEPTH = 6


@dataclass(frozen=True)
class ChainStep:
    node_id: str
    label: str
    node_type: str
    relation: str


def new_graph() -> nx.DiGraph:
    return nx.DiGraph()


def node_key(node_type: str, label: str) -> str:
    return f"{node_type}:{label.strip().lower()}"


def add_incident(
    graph: nx.DiGraph,
    incident_id: str,
    *,
    title: str,
    industry: str = "unknown",
    severity: str = "UNKNOWN",
    equipment: tuple[str, ...] = (),
    hazards: tuple[str, ...] = (),
    causes: tuple[str, ...] = (),
) -> str:
    """Add one incident and its related entities. Returns the incident node id."""
    incident_node = node_key("incident", incident_id)
    graph.add_node(incident_node, label=title, node_type="incident", industry=industry, severity=severity)

    for items, node_type, relation in (
        (equipment, "equipment", INVOLVED),
        (hazards, "hazard", INVOLVED),
        (causes, "cause", CAUSED_BY),
    ):
        for item in items:
            if not item.strip():
                continue
            key = node_key(node_type, item)
            graph.add_node(key, label=item.strip(), node_type=node_type)
            graph.add_edge(incident_node, key, relation=relation)
    return incident_node


def link_precursor(graph: nx.DiGraph, cause_node: str, effect_node: str) -> None:
    graph.add_edge(effect_node, cause_node, relation=PRECEDED_BY)


def find_precursor_chain(
    graph: nx.DiGraph, start: str, *, max_depth: int = MAX_CHAIN_DEPTH
) -> list[ChainStep]:
    """Breadth-first walk along causal edges from `start`, nearest cause first."""
    if start not in graph:
        return []

    steps: list[ChainStep] = []
    seen = {start}
    frontier = [(start, 0)]
    while frontier:
        node, depth = frontier.pop(0)
        if depth >= max_depth:
            continue
        for _, neighbour, data in graph.out_edges(node, data=True):
            relation = data.get("relation", "")
            if relation not in _CAUSAL_RELATIONS or neighbour in seen:
                continue
            seen.add(neighbour)
            attributes = graph.nodes[neighbour]
            steps.append(
                ChainStep(
                    node_id=neighbour,
                    label=attributes.get("label", neighbour),
                    node_type=attributes.get("node_type", "unknown"),
                    relation=relation,
                )
            )
            frontier.append((neighbour, depth + 1))
    return steps
