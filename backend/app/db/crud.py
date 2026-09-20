"""Every read and write against the analyses table."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AnalysisReport, AnalysisSummary, HistoryPage, SeverityTier
from .models import Analysis


async def create_analysis(session: AsyncSession, analysis_id: str, file_name: str) -> None:
    session.add(Analysis(id=analysis_id, file_name=file_name, status="processing"))
    await session.commit()


async def save_report(session: AsyncSession, report: AnalysisReport) -> None:
    row = await session.get(Analysis, report.analysis_id)
    if row is None:
        row = Analysis(id=report.analysis_id, file_name=report.file_name)
        session.add(row)
    row.status = "complete"
    row.severity = report.risk_score.tier.value
    row.industry = report.incident.industry
    row.risk_total = report.risk_score.total
    row.report = report.model_dump(mode="json")
    await session.commit()


async def mark_failed(session: AsyncSession, analysis_id: str, message: str) -> None:
    row = await session.get(Analysis, analysis_id)
    if row is None:
        return
    row.status = "failed"
    row.error = message[:1024]
    await session.commit()


async def get_report(session: AsyncSession, analysis_id: str) -> AnalysisReport | None:
    row = await session.get(Analysis, analysis_id)
    if row is None or row.report is None:
        return None
    return AnalysisReport.model_validate(row.report)


async def list_analyses(
    session: AsyncSession,
    *,
    page: int = 1,
    limit: int = 20,
    severity: str | None = None,
    industry: str | None = None,
) -> HistoryPage:
    filters = [Analysis.status == "complete"]
    if severity:
        filters.append(Analysis.severity == severity)
    if industry:
        filters.append(Analysis.industry == industry)

    total = await session.scalar(select(func.count()).select_from(Analysis).where(*filters)) or 0
    rows = await session.scalars(
        select(Analysis)
        .where(*filters)
        .order_by(Analysis.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    items = [
        AnalysisSummary(
            analysis_id=row.id,
            file_name=row.file_name,
            status=row.status,
            severity=SeverityTier(row.severity),
            risk_total=row.risk_total,
            industry=row.industry,
            created_at=row.created_at.isoformat(),
        )
        for row in rows
    ]
    return HistoryPage(items=items, total=total, page=page, limit=limit)


async def dashboard_stats(session: AsyncSession) -> dict[str, float | int]:
    """Aggregates for the dashboard stat cards, computed in the database."""
    complete = Analysis.status == "complete"
    return {
        "total_analyses": await session.scalar(select(func.count()).select_from(Analysis).where(complete))
        or 0,
        "critical_alerts": await session.scalar(
            select(func.count()).select_from(Analysis).where(complete, Analysis.severity == "CRITICAL")
        )
        or 0,
        "avg_risk_score": round(
            await session.scalar(select(func.avg(Analysis.risk_total)).where(complete)) or 0.0, 2
        ),
        "industries_covered": await session.scalar(
            select(func.count(func.distinct(Analysis.industry))).where(
                complete, Analysis.industry.is_not(None)
            )
        )
        or 0,
    }
