"""Graph wiring, node error semantics, and the SSE broker."""

from __future__ import annotations

import asyncio
import sys
import time

import pytest

import app.agents.nodes.risk_scorer  # noqa: F401  (populates sys.modules)
from app.agents.graph import GRAPH_CONFIG, RECURSION_LIMIT, route_after_scoring
from app.agents.nodes.base import NodeResult, node
from app.agents.nodes.error_handler import error_handler
from app.agents.nodes.risk_scorer import risk_scorer
from app.agents.state import initial_state
from app.models import RiskComponent, RiskScore, SeverityTier, StreamUpdate
from app.stream import StreamBroker

# `app.agents.nodes` re-exports each node under its module's name, shadowing it.
RISK_SCORER_MODULE = sys.modules["app.agents.nodes.risk_scorer"]

CRITICAL_SCORE = RiskScore(
    total=9.1,
    tier=SeverityTier.CRITICAL,
    components=[RiskComponent(name="Severity", score=9.5, weight=1.0, explanation="")],
    explanation="",
)


def state(**overrides):
    base = initial_state("a1", "report.pdf", "some incident text", time.monotonic())
    base.update(overrides)
    return base


class TestRouting:
    @pytest.mark.parametrize(
        ("total", "expected"),
        [(9.1, "priority"), (8.0, "priority"), (7.99, "standard"), (0.0, "standard")],
    )
    def test_score_selects_the_synthesis_path(self, total: float, expected: str) -> None:
        assert route_after_scoring(state(risk_score={"total": total})) == expected

    def test_an_error_beats_any_score(self) -> None:
        assert route_after_scoring(state(risk_score={"total": 9.9}, error="boom")) == "error"

    def test_missing_score_routes_to_standard(self) -> None:
        assert route_after_scoring(state(risk_score=None)) == "standard"


class TestNodeDecorator:
    async def test_successful_node_advances_the_stage_and_iteration(self) -> None:
        @node("demo", "working...")
        async def demo(_):
            return NodeResult(updates={"hazard_type": "electrical"}, message="done")

        result = await demo(state())
        assert result["hazard_type"] == "electrical"
        assert result["processing_stage"] == "demo"
        assert result["iteration_count"] == 1

    async def test_exception_is_captured_not_raised(self) -> None:
        @node("demo", "working...")
        async def demo(_):
            raise ValueError("retrieval exploded")

        result = await demo(state())
        # The exception message is logged, never surfaced: only stage and type escape.
        assert result["error"] == "demo: ValueError"
        assert "retrieval exploded" not in result["error"]
        assert result["processing_stage"] == "error_handler"

    async def test_node_is_a_noop_once_state_carries_an_error(self) -> None:
        @node("demo", "working...")
        async def demo(_):
            raise AssertionError("should never run")

        assert await demo(state(error="earlier failure")) == {}

    async def test_step_counter_advances_without_capping_a_long_pipeline(self) -> None:
        @node("demo", "working...")
        async def demo(_):
            return NodeResult(updates={}, message="done")

        # The seven-node pipeline must not be cut short by its own step counter;
        # runaway execution is bounded by the graph recursion limit instead.
        result = await demo(state(iteration_count=6))
        assert result["iteration_count"] == 7
        assert "error" not in result


class TestRecursionLimit:
    def test_limit_leaves_headroom_over_the_longest_path(self) -> None:
        longest_path = 7  # six pipeline nodes plus one synthesizer
        assert GRAPH_CONFIG["recursion_limit"] == RECURSION_LIMIT
        assert longest_path < RECURSION_LIMIT


class TestErrorHandler:
    async def test_produces_a_partial_report_rather_than_nothing(self) -> None:
        result = await error_handler(state(error="pattern_detector: qdrant down"))
        report = result["analysis_report"]
        assert report["analysis_id"] == "a1"
        assert report["risk_score"]["tier"] == "UNKNOWN"
        assert report["alerts"][0]["title"] == "Analysis incomplete"
        assert any("qdrant down" in warning for warning in report["warnings"])

    async def test_keeps_a_risk_score_that_was_already_computed(self) -> None:
        computed = {
            "total": 6.5,
            "tier": "HIGH",
            "components": [],
            "explanation": "computed before the failure",
        }
        result = await error_handler(state(error="alert synthesis failed", risk_score=computed))
        assert result["analysis_report"]["risk_score"]["total"] == 6.5


class TestStreamBroker:
    async def test_late_subscriber_is_replayed_the_whole_run(self) -> None:
        broker = StreamBroker()
        broker.open("a1")
        await broker.publish("a1", StreamUpdate(stage="document_router", status="completed"))
        await broker.publish("a1", StreamUpdate(stage="complete", status="completed"))
        broker.close("a1")

        stages = [update.stage async for update in broker.subscribe("a1")]
        assert stages == ["document_router", "complete"]

    async def test_live_subscriber_sees_updates_then_stops_at_the_terminal_event(self) -> None:
        broker = StreamBroker()
        broker.open("a1")

        received = []

        async def consume():
            async for update in broker.subscribe("a1"):
                received.append(update.stage)

        task = asyncio.create_task(consume())
        await asyncio.sleep(0.05)
        await broker.publish("a1", StreamUpdate(stage="risk_scorer", status="completed"))
        await broker.publish("a1", StreamUpdate(stage="complete", status="completed"))
        await asyncio.wait_for(task, timeout=2)
        assert received == ["risk_scorer", "complete"]

    async def test_unknown_analysis_yields_one_error_event(self) -> None:
        broker = StreamBroker()
        updates = [update async for update in broker.subscribe("nope")]
        assert [update.status for update in updates] == ["error"]

    async def test_publishing_to_a_closed_channel_is_harmless(self) -> None:
        broker = StreamBroker()
        await broker.publish("never-opened", StreamUpdate(stage="x", status="completed"))


class TestFrequencyCountsDocuments:
    """One report split into many chunks is one similar incident, not many."""

    @staticmethod
    def _state_with(chunks: list[str]):
        return state(
            incident={"severity_indicator": "HIGH"},
            similar_incidents=[
                {
                    "doc_id": f"c{i}",
                    "title": "t",
                    "similarity_score": 0.5,
                    "chunk_excerpt": "e",
                    "source_document": document,
                }
                for i, document in enumerate(chunks)
            ],
        )

    async def test_chunks_from_one_document_count_once(self, monkeypatch) -> None:
        captured = {}
        monkeypatch.setattr(
            RISK_SCORER_MODULE,
            "score_incident",
            lambda incident, **kwargs: captured.update(kwargs) or CRITICAL_SCORE,
        )
        await risk_scorer(self._state_with(["a.pdf", "a.pdf", "a.pdf"]))
        assert captured["similar_count"] == 1

    async def test_distinct_documents_are_counted_separately(self, monkeypatch) -> None:
        captured = {}
        monkeypatch.setattr(
            RISK_SCORER_MODULE,
            "score_incident",
            lambda incident, **kwargs: captured.update(kwargs) or CRITICAL_SCORE,
        )
        await risk_scorer(self._state_with(["a.pdf", "b.pdf", "a.pdf", "c.pdf"]))
        assert captured["similar_count"] == 3
