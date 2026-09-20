"""SQLAlchemy tables. One row per analysis; the report itself is stored as JSON.

Alerts live inside the report rather than in a second table: nothing queries
them independently, and the columns needed for filtering (severity, industry)
are denormalised onto the row.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    file_name: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(16), index=True, default="processing")
    severity: Mapped[str] = mapped_column(String(16), index=True, default="UNKNOWN")
    industry: Mapped[str | None] = mapped_column(String(64), index=True, default=None)
    risk_total: Mapped[float] = mapped_column(Float, default=0.0)
    report: Mapped[dict | None] = mapped_column(JSON, default=None)
    error: Mapped[str | None] = mapped_column(String(1024), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
