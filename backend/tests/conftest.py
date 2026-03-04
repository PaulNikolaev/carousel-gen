"""Pytest fixtures: test DB session with rollback, FastAPI client."""

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.main import app


def _test_database_url() -> str:
    return os.environ.get(
        "TEST_DATABASE_URL",
        os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/carousel"),
    )


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client with app dependency override: each test runs in a DB transaction that is rolled back."""
    test_url = _test_database_url()
    engine = create_async_engine(test_url, echo=False)
    async with engine.connect() as conn:
        await conn.begin()
        async with async_sessionmaker(
            bind=conn,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )() as session:

            async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
                yield session

            app.dependency_overrides[get_db] = override_get_db
            try:
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as ac:
                    yield ac
            finally:
                app.dependency_overrides.clear()
        await conn.rollback()
    await engine.dispose()
