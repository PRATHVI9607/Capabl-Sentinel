"""Publish a pipeline update to whichever SSE clients are watching this analysis."""

from __future__ import annotations

from ..models import StreamUpdate
from ..stream import broker


async def emit_stream_update(
    analysis_id: str, stage: str, status: str, message: str = "", data: dict | None = None
) -> None:
    """Non-blocking: an analysis with no subscriber still completes normally."""
    await broker.publish(analysis_id, StreamUpdate(stage=stage, status=status, message=message, data=data))
