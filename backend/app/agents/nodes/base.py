"""Shared node plumbing: streaming, error capture, and the iteration guard.

Every node gets identical start/complete/error semantics from one place instead
of eight copies of the same try/except.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from functools import wraps

from ...tools import emit_stream_update
from ..state import SentinelState

logger = logging.getLogger(__name__)


@dataclass
class NodeResult:
    """What a node produced: state updates plus what to tell the UI."""

    updates: dict = field(default_factory=dict)
    message: str = ""
    data: dict | None = None


NodeFunction = Callable[[SentinelState], Awaitable[NodeResult]]


def node(name: str, start_message: str) -> Callable[[NodeFunction], NodeFunction]:
    """Wrap a node body with streaming, error handling and the iteration guard.

    A node whose state already carries an error is a no-op: the failure is
    reported once, by the node that caused it, and the graph routes to
    `error_handler` after the risk scorer.

    `iteration_count` is telemetry only. Runaway execution is bounded by
    LangGraph's own `recursion_limit` (see `app/agents/graph.py`), which counts
    supersteps and therefore cannot be tripped by a legitimate long pipeline.
    """

    def decorator(function: NodeFunction) -> NodeFunction:
        @wraps(function)
        async def run(state: SentinelState) -> dict:
            if state.get("error"):
                return {}

            iteration = state.get("iteration_count", 0)
            analysis_id = state["analysis_id"]
            await emit_stream_update(analysis_id, name, "started", start_message)
            try:
                result = await function(state)
            except Exception as exc:  # the node boundary is where errors stop
                # The full traceback goes to the logs. What reaches the browser
                # names the stage and the exception type and nothing else: an
                # exception message can carry a path, a query or a credential.
                logger.exception("Node %s failed", name)
                reason = type(exc).__name__
                await emit_stream_update(analysis_id, name, "error", f"Stage failed ({reason})")
                return _fail(name, reason, iteration)

            await emit_stream_update(analysis_id, name, "completed", result.message, result.data)
            return {**result.updates, "processing_stage": name, "iteration_count": iteration + 1}

        return run

    return decorator


def _fail(name: str, message: str, iteration: int) -> dict:
    return {
        "error": f"{name}: {message}",
        "processing_stage": "error_handler",
        "iteration_count": iteration + 1,
    }
