"""Liveness endpoint. Also the UptimeRobot target that keeps Render warm."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from .. import __version__
from ..config import settings
from ..llm import any_provider_configured
from ..rag import vector_store

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "version": __version__,
        "environment": settings.environment,
        "llm_configured": any_provider_configured(),
        "vector_store_backend": vector_store.backend(),
        "vector_store_ready": vector_store.configured(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
