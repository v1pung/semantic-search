from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


@lru_cache(maxsize=1)
def get_engine(postgres_url: str) -> AsyncEngine:
    """Return a cached async engine. Created on first call, reused thereafter."""

    return create_async_engine(
        postgres_url,
        echo=False,
        pool_pre_ping=True,
    )


def get_session_factory(postgres_url: str) -> async_sessionmaker[AsyncSession]:
    """Return a session factory bound to the cached engine."""

    return async_sessionmaker(
        get_engine(postgres_url),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db(postgres_url: str) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a per-request AsyncSession."""
    
    factory = get_session_factory(postgres_url)
    async with factory() as session:
        yield session
