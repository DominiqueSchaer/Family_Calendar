from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .settings import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


@lru_cache
def get_engine():
    return create_async_engine(settings.database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory():
    return async_sessionmaker(bind=get_engine(), expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with get_session_factory()() as session:
        yield session
