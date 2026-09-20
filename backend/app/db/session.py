"""Async engine and session factory.

Defaults to SQLite so a fresh clone runs with no external database; point
DATABASE_URL at Supabase (postgresql+asyncpg://...) for the deployed app.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..config import settings
from .models import Base

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_models() -> None:
    """Create tables if they are missing.

    ponytail: no Alembic. One table, additive schema; add migrations when a
    column has to change shape in production.
    """
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
