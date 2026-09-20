"""Turn the CodeGraph index into an Obsidian vault and an architecture audit.

    codegraph sync .
    python scripts/codegraph_vault.py

Reads `.codegraph/codegraph.db` (built by https://github.com/colbymchenry/codegraph)
and writes:

    docs/codegraph-vault/     one note per module, one per layer, plus a canvas
    docs/CODE_AUDIT.md        cycles, layering violations, coupling, orphans

The vault is generated, never hand-edited: re-run this after `codegraph sync`.
"""

from __future__ import annotations

import ast
import json
import re
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx

REPO = Path(__file__).resolve().parent.parent
DB = REPO / ".codegraph" / "codegraph.db"
VAULT = REPO / "docs" / "codegraph-vault"
AUDIT = REPO / "docs" / "CODE_AUDIT.md"

# Only the backend is analysed: the frontend is being written concurrently, so
# any snapshot of it would be stale before it was read.
ROOT = "backend/app"
PACKAGE_ROOT = "backend"

# Edges below this resolution confidence are CodeGraph's dynamic-dispatch
# guesses. They are useful for exploration and too noisy for an audit.
MIN_EDGE_CONFIDENCE = 0.7

# Architectural layers, lowest first. An import from a lower layer to a higher
# one inverts the dependency direction and is reported as a violation.
LAYERS: list[tuple[str, str]] = [
    ("app/models", "Contracts"),
    ("app/config.py", "Contracts"),
    ("app/llm.py", "Providers"),
    ("app/cache", "Providers"),
    ("app/db", "Providers"),
    ("app/stream.py", "Providers"),
    ("app/rag", "Retrieval"),
    ("app/ingest", "Retrieval"),
    ("app/knowledge_graph", "Retrieval"),
    ("app/tools", "Tools"),
    ("app/agents", "Orchestration"),
    ("app/pipeline.py", "Orchestration"),
    ("app/deps.py", "Transport"),
    ("app/api", "Transport"),
    ("app/main.py", "Transport"),
]
LAYER_ORDER = ["Contracts", "Providers", "Retrieval", "Tools", "Orchestration", "Transport"]

# Coupling above these thresholds is worth a look, not automatically wrong.
HIGH_FAN_IN = 8
HIGH_FAN_OUT = 8


@dataclass
class Module:
    path: str
    dotted: str
    layer: str
    docstring: str = ""
    lines: int = 0
    symbols: list[tuple[str, str, int]] = field(default_factory=list)
    external: set[str] = field(default_factory=set)


def module_docstring(path: Path) -> str:
    """First line of the module docstring. CodeGraph does not capture these."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return ""
    lines = (ast.get_docstring(tree) or "").strip().splitlines()
    return lines[0] if lines else ""


def layer_for(path: str) -> str:
    relative = path[len(PACKAGE_ROOT) + 1 :]
    for prefix, layer in LAYERS:
        if relative == prefix or relative.startswith(prefix + "/"):
            return layer
    return "Unassigned"


def dotted_name(path: str) -> str:
    stem = path[len(PACKAGE_ROOT) + 1 :].removesuffix(".py")
    return stem.replace("/", ".").removesuffix(".__init__")


_IMPORTED_NAMES = re.compile(r"^from\s+\S+\s+import\s+(.+)$", re.S)


def _module_base(name: str, from_path: str) -> str | None:
    """Filesystem prefix a dotted or relative module name points at."""
    if name.startswith("."):
        depth = len(name) - len(name.lstrip("."))
        package = Path(from_path).parent
        for _ in range(depth - 1):
            package = package.parent
        return str(package / name[depth:].replace(".", "/")).replace("\\", "/").rstrip("/")
    if name.startswith("app."):
        return f"{PACKAGE_ROOT}/" + name.replace(".", "/")
    return None


def _as_module(candidate: str, known: dict[str, str]) -> str | None:
    for suffix in (".py", "/__init__.py"):
        if (candidate + suffix) in known:
            return candidate + suffix
    return None


def resolve_import(name: str, signature: str, from_path: str, known: dict[str, str]) -> list[str]:
    """First-party modules an import statement actually reaches.

    `from .api import analyze, health` names the package, but the dependency is
    on the submodules. Resolving only the package would report every router as
    imported by nothing -- a false "delete this" finding. So the imported names
    are resolved as submodules too, and the package itself is only returned when
    none of them is one (`from .config import settings`).
    """
    base = _module_base(name, from_path)
    if base is None:
        return []

    submodules = []
    match = _IMPORTED_NAMES.match((signature or "").strip())
    if match:
        for fragment in match.group(1).replace("(", "").replace(")", "").split(","):
            imported = fragment.strip().split(" as ")[0].strip()
            if imported and imported != "*" and (found := _as_module(f"{base}/{imported}", known)):
                submodules.append(found)
    if submodules:
        return submodules

    direct = _as_module(base, known)
    return [direct] if direct else []


def load() -> tuple[dict[str, Module], nx.DiGraph]:
    if not DB.exists():
        raise SystemExit(f"No index at {DB}. Run: codegraph init . (or codegraph sync .)")

    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    files = {
        row[0]: row
        for row in db.execute(
            "SELECT file_path, start_line, end_line FROM nodes " "WHERE kind='file' AND file_path LIKE ?",
            (ROOT + "%",),
        )
    }
    modules = {
        path: Module(
            path=path,
            dotted=dotted_name(path),
            layer=layer_for(path),
            docstring=module_docstring(REPO / path),
            lines=row[2] or 0,
        )
        for path, row in files.items()
    }

    for path, kind, name, line in db.execute(
        "SELECT file_path, kind, name, start_line FROM nodes "
        "WHERE file_path LIKE ? AND kind IN ('function','class','method','constant') "
        "ORDER BY file_path, start_line",
        (ROOT + "%",),
    ):
        if path in modules:
            modules[path].symbols.append((kind, name, line))

    graph = nx.DiGraph()
    for module in modules.values():
        graph.add_node(module.path, layer=module.layer, dotted=module.dotted)

    # Imports: the authoritative dependency signal.
    for source_path, name, signature in db.execute(
        "SELECT file_path, name, signature FROM nodes WHERE kind='import' AND file_path LIKE ?",
        (ROOT + "%",),
    ):
        if source_path not in modules:
            continue
        targets = resolve_import(name, signature, source_path, files)
        if not targets:
            root_package = name.lstrip(".").split(".")[0]
            if root_package and not name.startswith("."):
                modules[source_path].external.add(root_package)
        for target in targets:
            if target != source_path:
                _bump(graph, source_path, target, "imports")

    # Call/reference edges are admitted only where an import already connects the
    # two modules. CodeGraph resolves call targets by name, so a dict `.get()`
    # matches `cache.client.get` at 0.7 confidence and invents a dependency.
    # Python cannot reach another module without importing it, or its package,
    # so the import graph is the gate.
    importable = {(a, b) for a, b in graph.edges()}
    for source, target in list(importable):
        package = target.rsplit("/", 1)[0] + "/__init__.py"
        if package in modules:
            importable.add((source, package))
    for source, target in list(graph.edges()):
        if target.endswith("/__init__.py"):
            prefix = target[: -len("/__init__.py")]
            importable.update((source, other) for other in modules if other.startswith(prefix + "/"))

    for source_path, target_path, kind, metadata in db.execute(
        "SELECT s.file_path, t.file_path, e.kind, e.metadata FROM edges e "
        "JOIN nodes s ON s.id=e.source JOIN nodes t ON t.id=e.target "
        "WHERE e.kind IN ('calls','references','instantiates') "
        "AND s.file_path LIKE ? AND t.file_path LIKE ?",
        (ROOT + "%", ROOT + "%"),
    ):
        if source_path == target_path or source_path not in modules or target_path not in modules:
            continue
        if (source_path, target_path) not in importable:
            continue
        confidence = 1.0
        if metadata:
            try:
                confidence = float(json.loads(metadata).get("confidence", 1.0))
            except (ValueError, TypeError):
                confidence = 1.0
        if confidence >= MIN_EDGE_CONFIDENCE:
            _bump(graph, source_path, target_path, kind)

    return modules, graph


def _bump(graph: nx.DiGraph, source: str, target: str, kind: str) -> None:
    if graph.has_edge(source, target):
        graph.edges[source, target]["weight"] += 1
        graph.edges[source, target]["kinds"].add(kind)
    else:
        graph.add_edge(source, target, weight=1, kinds={kind})


def findings(modules: dict[str, Module], graph: nx.DiGraph) -> dict[str, list]:
    rank = {layer: index for index, layer in enumerate(LAYER_ORDER)}

    violations = []
    for source, target in graph.edges():
        source_rank = rank.get(modules[source].layer, -1)
        target_rank = rank.get(modules[target].layer, -1)
        if source_rank >= 0 and target_rank >= 0 and target_rank > source_rank:
            violations.append((modules[source], modules[target]))

    cycles = [cycle for cycle in nx.simple_cycles(graph) if len(cycle) > 1]

    orphans = [
        modules[path]
        for path in graph.nodes()
        if graph.in_degree(path) == 0
        and not path.endswith("__init__.py")
        and Path(path).name not in {"main.py"}
    ]

    hubs = sorted(
        (modules[path] for path in graph.nodes() if graph.in_degree(path) >= HIGH_FAN_IN),
        key=lambda m: -graph.in_degree(m.path),
    )
    spreaders = sorted(
        (modules[path] for path in graph.nodes() if graph.out_degree(path) >= HIGH_FAN_OUT),
        key=lambda m: -graph.out_degree(m.path),
    )

    # config and models are imported by nearly everything; leaving them in makes
    # Louvain return one blob. Clustering the rest shows real feature coupling.
    feature_graph = graph.subgraph(
        [p for p in graph.nodes() if modules[p].layer != "Contracts"]
    ).to_undirected()
    detected = nx.community.louvain_communities(feature_graph, seed=7)
    split = []
    for community in detected:
        layers = {modules[path].layer for path in community}
        if len(layers) > 1 and len(community) > 2:
            split.append((sorted(layers), sorted(modules[p].dotted for p in community)))

    return {
        "violations": violations,
        "cycles": cycles,
        "orphans": orphans,
        "hubs": hubs,
        "spreaders": spreaders,
        "communities": detected,
        "split": split,
    }


def write_vault(modules: dict[str, Module], graph: nx.DiGraph, found: dict) -> int:
    VAULT.mkdir(parents=True, exist_ok=True)
    (VAULT / "modules").mkdir(exist_ok=True)
    (VAULT / "layers").mkdir(exist_ok=True)

    community_of = {path: index for index, group in enumerate(found["communities"]) for path in group}
    by_layer: dict[str, list[Module]] = defaultdict(list)
    for module in modules.values():
        by_layer[module.layer].append(module)

    for module in modules.values():
        dependencies = sorted(graph.successors(module.path), key=lambda p: modules[p].dotted)
        dependents = sorted(graph.predecessors(module.path), key=lambda p: modules[p].dotted)
        lines = [
            "---",
            f"tags: [codegraph, module, layer/{module.layer.lower()}]",
            f"layer: {module.layer}",
            f"source: {module.path}",
            f"fan_in: {len(dependents)}",
            f"fan_out: {len(dependencies)}",
            f"symbols: {len(module.symbols)}",
            f"community: {community_of.get(module.path, -1)}",
            "---",
            "",
            f"# `{module.dotted}`",
            "",
            f"> {module.docstring or '_No module docstring._'}",
            "",
            f"Layer: [[{module.layer}]] · `{module.path}` · {module.lines} lines · "
            f"{len(module.symbols)} symbols",
            "",
        ]

        lines += ["## Depends on", ""]
        lines += (
            [
                f"- [[{modules[p].dotted}]] — {', '.join(sorted(graph.edges[module.path, p]['kinds']))}"
                f" ×{graph.edges[module.path, p]['weight']}"
                for p in dependencies
            ]
            or ["_Nothing in this package._"]
        ) + [""]

        lines += ["## Depended on by", ""]
        lines += (
            [
                f"- [[{modules[p].dotted}]] — {', '.join(sorted(graph.edges[p, module.path]['kinds']))}"
                f" ×{graph.edges[p, module.path]['weight']}"
                for p in dependents
            ]
            or ["_Nothing — an entry point, or unused._"]
        ) + [""]

        if module.symbols:
            lines += ["## Symbols", "", "| Kind | Name | Line |", "|---|---|---|"]
            lines += [f"| {k} | `{n}` | {ln} |" for k, n, ln in module.symbols] + [""]

        if module.external:
            lines += ["## External packages", "", ", ".join(f"`{e}`" for e in sorted(module.external)), ""]

        (VAULT / "modules" / f"{module.dotted}.md").write_text("\n".join(lines), encoding="utf-8")

    for layer in LAYER_ORDER + ["Unassigned"]:
        members = sorted(by_layer.get(layer, []), key=lambda m: m.dotted)
        if not members:
            continue
        lines = [
            "---",
            "tags: [codegraph, layer]",
            "---",
            "",
            f"# {layer}",
            "",
            f"{len(members)} modules. Layer "
            f"{LAYER_ORDER.index(layer) if layer in LAYER_ORDER else '—'} of "
            f"{len(LAYER_ORDER)}; imports may point down this list, never up.",
            "",
            "| Module | In | Out | Symbols | Purpose |",
            "|---|---|---|---|---|",
        ]
        lines += [
            f"| [[{m.dotted}]] | {graph.in_degree(m.path)} | {graph.out_degree(m.path)} | "
            f"{len(m.symbols)} | {m.docstring or ''} |"
            for m in members
        ]
        (VAULT / "layers" / f"{layer}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    index = [
        "---",
        "tags: [codegraph, index]",
        "---",
        "",
        "# SENTINEL backend — code map",
        "",
        f"Generated from the CodeGraph index by `scripts/codegraph_vault.py`. "
        f"{len(modules)} modules, {graph.number_of_edges()} dependencies.",
        "",
        "Open this folder as an Obsidian vault. Graph view shows the real dependency",
        "structure; `graph.canvas` lays it out by layer.",
        "",
        "## Layers",
        "",
        "Dependencies point **down** this list. An edge pointing up is a violation",
        "and is listed in [[../CODE_AUDIT|the audit]].",
        "",
    ]
    for layer in LAYER_ORDER + ["Unassigned"]:
        members = by_layer.get(layer, [])
        if members:
            index.append(
                f"{LAYER_ORDER.index(layer) if layer in LAYER_ORDER else '—'}. "
                f"[[{layer}]] — {len(members)} modules"
            )
    index += ["", "## Most depended on", ""]
    ranked = sorted(modules.values(), key=lambda m: -graph.in_degree(m.path))[:10]
    index += [f"- [[{m.dotted}]] — {graph.in_degree(m.path)} dependents" for m in ranked]
    (VAULT / "_INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")

    write_canvas(graph, by_layer)
    return len(modules) + len([lay for lay in by_layer if by_layer[lay]]) + 1


def write_canvas(graph: nx.DiGraph, by_layer: dict[str, list[Module]]) -> None:
    """An Obsidian canvas with one column per layer, dependencies drawn between."""
    nodes, edges = [], []
    column_width, card_width, card_height, gap = 520, 400, 90, 40

    position = {}
    for column, layer in enumerate(LAYER_ORDER + ["Unassigned"]):
        members = sorted(by_layer.get(layer, []), key=lambda m: -graph.in_degree(m.path))
        if not members:
            continue
        x = column * column_width
        nodes.append(
            {
                "id": f"group-{layer}",
                "type": "group",
                "label": layer,
                "x": x - 30,
                "y": -80,
                "width": card_width + 60,
                "height": len(members) * (card_height + gap) + 100,
            }
        )
        for row, module in enumerate(members):
            y = row * (card_height + gap)
            position[module.path] = (x, y)
            nodes.append(
                {
                    "id": module.path,
                    "type": "file",
                    "file": f"modules/{module.dotted}.md",
                    "x": x,
                    "y": y,
                    "width": card_width,
                    "height": card_height,
                }
            )

    for source, target in graph.edges():
        if source in position and target in position:
            edges.append(
                {
                    "id": f"{source}->{target}",
                    "fromNode": source,
                    "fromSide": "right",
                    "toNode": target,
                    "toSide": "left",
                }
            )
    canvas = json.dumps({"nodes": nodes, "edges": edges}, indent=1)
    (VAULT / "graph.canvas").write_text(canvas, encoding="utf-8")


def write_audit(modules: dict[str, Module], graph: nx.DiGraph, found: dict) -> None:
    def name(path: str) -> str:
        return f"`{modules[path].dotted}`"

    lines = [
        "# Architecture audit",
        "",
        "Generated by `scripts/codegraph_vault.py` from the CodeGraph index.",
        "Re-run after `codegraph sync .`; do not hand-edit.",
        "",
        f"**{len(modules)} modules · {graph.number_of_edges()} internal dependencies · "
        f"{sum(len(m.symbols) for m in modules.values())} symbols**",
        "",
        "Edges below "
        f"{MIN_EDGE_CONFIDENCE:.0%} resolution confidence are excluded: those are CodeGraph's "
        "dynamic-dispatch guesses, useful for exploration and too noisy for an audit.",
        "",
        "---",
        "",
        "## Import cycles",
        "",
    ]
    if found["cycles"]:
        lines += [f"- {' → '.join(name(p) for p in cycle)} → {name(cycle[0])}" for cycle in found["cycles"]]
    else:
        lines.append("None. The module graph is a DAG.")

    lines += [
        "",
        "## Layering violations",
        "",
        "Dependencies must point down the layer list "
        f"({' → '.join(LAYER_ORDER)}). An edge pointing up inverts control.",
        "",
    ]
    if found["violations"]:
        lines += [
            f"- {name(s.path)} ({s.layer}) → {name(t.path)} ({t.layer})" for s, t in found["violations"]
        ]
    else:
        lines.append("None. Every dependency points down or sideways.")

    lines += ["", "## Coupling", "", f"### Most depended on (fan-in ≥ {HIGH_FAN_IN})", ""]
    if found["hubs"]:
        lines += ["| Module | Dependents | Layer |", "|---|---|---|"]
        lines += [f"| {name(m.path)} | {graph.in_degree(m.path)} | {m.layer} |" for m in found["hubs"]]
        lines += [
            "",
            "High fan-in on a Contracts or Providers module is the point of the layer. "
            "High fan-in higher up the stack means a change there ripples widely.",
        ]
    else:
        lines.append(f"No module has {HIGH_FAN_IN} or more dependents.")

    lines += ["", f"### Widest reach (fan-out ≥ {HIGH_FAN_OUT})", ""]
    if found["spreaders"]:
        lines += ["| Module | Depends on | Layer |", "|---|---|---|"]
        lines += [
            f"| {name(m.path)} | {graph.out_degree(m.path)} | {m.layer} |" for m in found["spreaders"]
        ]
    else:
        lines.append(f"No module depends on {HIGH_FAN_OUT} or more others.")

    lines += [
        "",
        "## Modules nothing imports",
        "",
        "Entry points and framework-dispatched modules appear here legitimately. "
        "Anything else is a candidate for deletion.",
        "",
    ]
    lines += [f"- {name(m.path)} — {m.docstring or 'no docstring'}" for m in found["orphans"]] or ["None."]

    lines += [
        "",
        "## Detected communities vs declared layers",
        "",
        "Louvain clustering over the dependency graph, compared with the package "
        "layout. A community spanning layers is where the code actually couples "
        "regardless of where the files live.",
        "",
    ]
    if found["split"]:
        for layers, members in found["split"]:
            lines.append(f"- **{' + '.join(layers)}** — {', '.join('`' + m + '`' for m in members)}")
    else:
        lines.append("Every detected community sits inside one declared layer.")

    lines += ["", "---", ""]
    lines += ["See [[docs/codegraph-vault/_INDEX|the code map]] for the navigable version.", ""]
    AUDIT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    modules, graph = load()
    found = findings(modules, graph)
    notes = write_vault(modules, graph, found)
    write_audit(modules, graph, found)

    print(f"Modules:     {len(modules)}")
    print(f"Dependencies:{graph.number_of_edges():>4}")
    print(f"Communities: {len(found['communities'])}")
    print(f"Cycles:      {len(found['cycles'])}")
    print(f"Violations:  {len(found['violations'])}")
    print(f"Orphans:     {len(found['orphans'])}")
    print(f"\nVault: {VAULT.relative_to(REPO)}/ ({notes} notes + graph.canvas)")
    print(f"Audit: {AUDIT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
