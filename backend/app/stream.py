"""In-process pub/sub between the analysis background task and SSE subscribers.

The upload response returns before the client opens the event stream, so the
channel is created at upload time and every update is kept. A subscriber that
connects late -- or reconnects -- is replayed the updates it missed and then
tails the live ones.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from .config import settings
from .models import StreamUpdate

# How long a finished channel stays replayable after the last update.
CHANNEL_TTL_SECONDS = 300.0
HEARTBEAT_SECONDS = 25.0


@dataclass
class _Channel:
    history: list[StreamUpdate] = field(default_factory=list)
    subscribers: set[asyncio.Queue[StreamUpdate]] = field(default_factory=set)
    done: bool = False
    closed_at: float = 0.0


class StreamBroker:
    """One channel per analysis. Not shared across processes -- see note below.

    ponytail: a dict, not Redis pub/sub. The analysis task and its SSE stream
    are always in the same process today. Swap in Redis if the API is ever
    scaled past one instance.
    """

    def __init__(self) -> None:
        self._channels: dict[str, _Channel] = {}

    def open(self, analysis_id: str) -> None:
        self._evict_expired()
        self._channels[analysis_id] = _Channel()

    async def publish(self, analysis_id: str, update: StreamUpdate) -> None:
        channel = self._channels.get(analysis_id)
        if channel is None:
            return
        channel.history.append(update)
        for queue in channel.subscribers:
            queue.put_nowait(update)

    def close(self, analysis_id: str) -> None:
        channel = self._channels.get(analysis_id)
        if channel is None:
            return
        channel.done = True
        channel.closed_at = time.monotonic()

    async def subscribe(self, analysis_id: str) -> AsyncIterator[StreamUpdate]:
        """Yield past then live updates, ending once the analysis is finished."""
        channel = self._channels.get(analysis_id)
        if channel is None:
            yield StreamUpdate(stage="error", status="error", message="Unknown analysis id")
            return

        queue: asyncio.Queue[StreamUpdate] = asyncio.Queue()
        replayed = list(channel.history)
        channel.subscribers.add(queue)
        deadline = time.monotonic() + settings.stream_timeout_seconds
        try:
            for update in replayed:
                yield update
            if channel.done and _is_terminal(replayed):
                return
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    # Bounded, so an abandoned connection cannot be held open forever.
                    yield StreamUpdate(stage="error", status="error", message="Stream timed out")
                    return
                try:
                    update = await asyncio.wait_for(queue.get(), timeout=min(HEARTBEAT_SECONDS, remaining))
                except TimeoutError:
                    yield StreamUpdate(stage="heartbeat", status="alive")
                    continue
                yield update
                if update.stage in _TERMINAL_STAGES:
                    return
        finally:
            channel.subscribers.discard(queue)

    def _evict_expired(self) -> None:
        cutoff = time.monotonic() - CHANNEL_TTL_SECONDS
        for analysis_id, channel in list(self._channels.items()):
            if channel.done and not channel.subscribers and channel.closed_at < cutoff:
                del self._channels[analysis_id]


_TERMINAL_STAGES = {"complete", "error"}


def _is_terminal(updates: list[StreamUpdate]) -> bool:
    return bool(updates) and updates[-1].stage in _TERMINAL_STAGES


broker = StreamBroker()
