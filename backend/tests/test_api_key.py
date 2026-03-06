"""Tests for API key middleware: 401 when key missing/wrong, 200 with X-API-Key header, health excluded."""

import pytest
from httpx import AsyncClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Ensure get_settings() is re-read in tests that set API_KEY."""
    get_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()


async def test_no_key_returns_401_when_api_key_set(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When API_KEY is set, request without key returns 401."""
    monkeypatch.setenv("API_KEY", "secret-key")
    get_settings.cache_clear()
    response = await client.get("/api/v1/carousels")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key", "code": 401}


async def test_valid_header_returns_200(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When API_KEY is set, request with X-API-Key header returns 200."""
    monkeypatch.setenv("API_KEY", "secret-key")
    get_settings.cache_clear()
    response = await client.get(
        "/api/v1/carousels",
        headers={"X-API-Key": "secret-key"},
    )
    assert response.status_code == 200


async def test_health_excluded_from_auth(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When API_KEY is set, GET /api/v1/health without key returns 200."""
    monkeypatch.setenv("API_KEY", "secret-key")
    get_settings.cache_clear()
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_api_key_empty_skips_check(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When API_KEY is not set, request without key returns 200 (backward compatible)."""
    monkeypatch.setenv("API_KEY", "")
    get_settings.cache_clear()
    response = await client.get("/api/v1/carousels")
    assert response.status_code == 200
