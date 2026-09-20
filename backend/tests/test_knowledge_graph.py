"""Causal graph construction, traversal and persistence."""

from __future__ import annotations

import networkx as nx

from app.knowledge_graph import graph as kg
from app.knowledge_graph import serializer


def build() -> nx.DiGraph:
    graph = kg.new_graph()
    kg.add_incident(
        graph,
        "osha-2021-0412.pdf",
        title="Stamping press fatality",
        industry="manufacturing",
        severity="CRITICAL",
        equipment=("hydraulic press", "conveyor"),
        hazards=("amputation",),
        causes=("guard removed", "did not verify"),
    )
    return graph


class TestConstruction:
    def test_incident_links_to_each_related_entity(self) -> None:
        graph = build()
        incident = kg.node_key("incident", "osha-2021-0412.pdf")
        assert graph.nodes[incident]["severity"] == "CRITICAL"
        assert set(graph.successors(incident)) == {
            kg.node_key("equipment", "hydraulic press"),
            kg.node_key("equipment", "conveyor"),
            kg.node_key("hazard", "amputation"),
            kg.node_key("cause", "guard removed"),
            kg.node_key("cause", "did not verify"),
        }

    def test_relations_distinguish_involvement_from_causation(self) -> None:
        graph = build()
        incident = kg.node_key("incident", "osha-2021-0412.pdf")
        relations = {
            graph.nodes[target]["node_type"]: data["relation"]
            for _, target, data in graph.out_edges(incident, data=True)
        }
        assert relations["equipment"] == kg.INVOLVED
        assert relations["hazard"] == kg.INVOLVED
        assert relations["cause"] == kg.CAUSED_BY

    def test_node_keys_are_case_and_whitespace_insensitive(self) -> None:
        assert kg.node_key("equipment", "  Hydraulic Press ") == kg.node_key("equipment", "hydraulic press")

    def test_blank_entities_are_skipped(self) -> None:
        graph = kg.new_graph()
        kg.add_incident(graph, "d.pdf", title="t", equipment=("", "   ", "press"))
        assert kg.node_key("equipment", "press") in graph
        assert graph.number_of_nodes() == 2

    def test_the_same_entity_across_incidents_is_one_node(self) -> None:
        graph = kg.new_graph()
        kg.add_incident(graph, "a.pdf", title="a", equipment=("press",))
        kg.add_incident(graph, "b.pdf", title="b", equipment=("press",))
        assert graph.in_degree(kg.node_key("equipment", "press")) == 2


class TestTraversal:
    def test_causal_edges_are_followed_and_involvement_is_not(self) -> None:
        graph = build()
        incident = kg.node_key("incident", "osha-2021-0412.pdf")
        labels = [step.label for step in kg.find_precursor_chain(graph, incident)]
        assert sorted(labels) == ["did not verify", "guard removed"]

    def test_precursor_links_extend_the_chain(self) -> None:
        graph = build()
        hazard = kg.node_key("hazard", "amputation")
        condition = kg.node_key("condition", "unguarded nip point")
        graph.add_node(condition, label="unguarded nip point", node_type="condition")
        kg.link_precursor(graph, condition, hazard)

        chain = kg.find_precursor_chain(graph, hazard)
        assert [step.label for step in chain] == ["unguarded nip point"]
        assert chain[0].relation == kg.PRECEDED_BY

    def test_depth_is_bounded(self) -> None:
        graph = kg.new_graph()
        keys = [kg.node_key("cause", f"c{i}") for i in range(10)]
        for index, key in enumerate(keys):
            graph.add_node(key, label=f"c{index}", node_type="cause")
        for earlier, later in zip(keys, keys[1:], strict=False):
            kg.link_precursor(graph, later, earlier)
        assert len(kg.find_precursor_chain(graph, keys[0], max_depth=3)) == 3

    def test_a_cycle_does_not_loop_forever(self) -> None:
        graph = kg.new_graph()
        a, b = kg.node_key("cause", "a"), kg.node_key("cause", "b")
        for key, label in ((a, "a"), (b, "b")):
            graph.add_node(key, label=label, node_type="cause")
        kg.link_precursor(graph, b, a)
        kg.link_precursor(graph, a, b)
        # Terminates, and the start node is not reported as its own precursor.
        assert [step.label for step in kg.find_precursor_chain(graph, a)] == ["b"]

    def test_unknown_start_node_yields_nothing(self) -> None:
        assert kg.find_precursor_chain(build(), "incident:not-here") == []


class TestPersistence:
    def test_round_trip_preserves_nodes_edges_and_attributes(self, tmp_path) -> None:
        graph = build()
        path = tmp_path / "kg.json"
        serializer.save(graph, path)

        serializer.load.cache_clear()
        restored = serializer.load(path)
        assert restored.number_of_nodes() == graph.number_of_nodes()
        assert restored.number_of_edges() == graph.number_of_edges()

        incident = kg.node_key("incident", "osha-2021-0412.pdf")
        assert restored.nodes[incident]["severity"] == "CRITICAL"
        assert [s.label for s in kg.find_precursor_chain(restored, incident)]

    def test_missing_file_loads_as_an_empty_graph(self, tmp_path) -> None:
        serializer.load.cache_clear()
        assert serializer.load(tmp_path / "absent.json").number_of_nodes() == 0
