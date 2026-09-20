"""Past analyses: the list behind the incident explorer and the dashboard stats."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from ..db import crud
from ..deps import DbSession
from ..models import AnalysisReport, HistoryPage, SeverityTier

router = APIRouter(tags=["history"])

MAX_PAGE_SIZE = 100


@router.get("/history", response_model=HistoryPage)
async def list_history(
    session: DbSession,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
    severity: SeverityTier | None = None,
    industry: str | None = None,
) -> HistoryPage:
    return await crud.list_analyses(
        session,
        page=page,
        limit=limit,
        severity=severity.value if severity else None,
        industry=industry,
    )


@router.get("/history/stats")
async def history_stats(session: DbSession) -> dict[str, float | int]:
    """Aggregates for the dashboard stat cards."""
    return await crud.dashboard_stats(session)


@router.get("/history/{analysis_id}", response_model=AnalysisReport)
async def get_history_entry(analysis_id: str, session: DbSession) -> AnalysisReport:
    report = await crud.get_report(session, analysis_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found")
    return report
