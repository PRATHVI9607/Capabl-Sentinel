"""Key/value cache over the Upstash REST API, with an in-process fallback.

The fallback keeps local development and tests free of external services; it is
per-process, so on multi-instance deploys configure Upstash.
"""

from __future__ import annotations

import logging
import time

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

_local: dict[str, tuple[str, float]] = {}


def _configured() -> bool:
    return bool(settings.upstash_redis_rest_url and settings.upstash_redis_rest_token)


async def _command(*parts: str | int) -> object:
    url = settings.upstash_redis_rest_url.rstrip("/") + "/" + "/".join(str(p) for p in parts)
    headers = {"Authorization": f"Bearer {settings.upstash_redis_rest_token}"}
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("result")


def _local_get(key: str) -> str | None:
    entry = _local.get(key)
    if entry is None:
        return None
    value, expires_at = entry
    if expires_at and expires_at < time.time():
        _local.pop(key, None)
        return None
    return value


async def get(key: str) -> str | None:
    if not _configured():
        return _local_get(key)
    try:
        result = await _command("get", key)
    except Exception as exc:  # noqa: BLE001 - a cache miss is always an acceptable outcome
        logger.warning("Cache get failed for %s: %s", key, exc)
        return None
    return None if result is None else str(result)


async def set(key: str, value: str, ttl_seconds: int) -> None:  # noqa: A001 - mirrors the Redis verb
    if not _configured():
        _local[key] = (value, time.time() + ttl_seconds)
        return
    try:
        await _command("set", key, value, "ex", ttl_seconds)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cache set failed for %s: %s", key, exc)


async def incr_with_expiry(key: str, ttl_seconds: int) -> int:
    """Increment `key`, setting its TTL on first use. Returns the new count."""
    if not _configured():
        current = int(_local_get(key) or 0) + 1
        _, expires_at = _local.get(key, ("", 0.0))
        if not expires_at or expires_at < time.time():
            expires_at = time.time() + ttl_seconds
        _local[key] = (str(current), expires_at)
        return current
    try:
        count = int(await _command("incr", key) or 0)
        if count == 1:
            await _command("expire", key, ttl_seconds)
        return count
    except Exception as exc:  # noqa: BLE001 - never let the cache take the request down
        logger.warning("Cache incr failed for %s: %s", key, exc)
        return 0


def reset_local() -> None:
    """Test helper: drop the in-process fallback state."""
    _local.clear()
