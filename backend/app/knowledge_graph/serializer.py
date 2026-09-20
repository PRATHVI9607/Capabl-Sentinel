"""Persist the knowledge graph as JSON on disk.

ponytail: a file, not a database table. The graph is built once by the ingest
script and read-only at runtime, so it ships with the repo like the BM25 index.
"""

from __future__ import annotations

import inspect
import json
import logging
from functools import lru_cache
from pathlib import Path

import networkx as nx

from ..config import settings

logger = logging.getLogger(__name__)

GRAPH_FILENAME = "knowledge_graph.json"

# networkx renamed this keyword from `link` to `edges` in 3.4. Detect it once so
# the serialised format stays the same across both.
_LINK_KEY = (
    {"edges": "links"} if "edges" in inspect.signature(nx.node_link_data).parameters else {"link": "links"}
)


def graph_path() -> Path:
    return settings.data_dir / GRAPH_FILENAME


def save(graph: nx.DiGraph, path: Path | None = None) -> None:
    target = path or graph_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    # networkx 3.3 names this key "links"; 3.4 renamed the keyword to `edges` and
    # will default to "edges". Both ends pass it explicitly so the format is fixed
    # by this module rather than by the installed version.
    target.write_text(json.dumps(nx.node_link_data(graph, **_LINK_KEY)), encoding="utf-8")


@lru_cache(maxsize=1)
def load(path: Path | None = None) -> nx.DiGraph:
    """Load the graph, or an empty one if it has not been built yet."""
    source = path or graph_path()
    if not source.exists():
        logger.warning("No knowledge graph at %s; causal chains will be empty.", source)
        return nx.DiGraph()
    payload = json.loads(source.read_text(encoding="utf-8"))
    return nx.node_link_graph(payload, directed=True, **_LINK_KEY)
