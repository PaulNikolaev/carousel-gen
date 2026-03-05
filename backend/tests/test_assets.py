"""Pytest + httpx tests for POST /api/v1/assets/upload (multipart, field 'file')."""

import io
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.api.assets import MAX_UPLOAD_SIZE, _get_storage
from app.main import app


@pytest.fixture
def mock_storage():
    """StorageService mock: upload_file returns (url, key) without calling S3."""
    mock = AsyncMock()
    mock.upload_file = AsyncMock(return_value=("https://storage.example/asset/abc123.png", "assets/abc123.png"))
    return mock


@pytest.mark.asyncio
async def test_upload_asset_200(client: AsyncClient, mock_storage) -> None:
    """POST /assets/upload with valid file returns 200 and {url, key}."""
    app.dependency_overrides[_get_storage] = lambda: mock_storage
    try:
        png_header = b"\x89PNG\r\n\x1a\n"
        files = {"file": ("image.png", io.BytesIO(png_header + b"\x00" * 100), "image/png")}
        response = await client.post("/api/v1/assets/upload", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "key" in data
        assert data["url"] == "https://storage.example/asset/abc123.png"
        assert data["key"] == "assets/abc123.png"
    finally:
        app.dependency_overrides.pop(_get_storage, None)


@pytest.mark.asyncio
async def test_upload_asset_missing_file_400(client: AsyncClient) -> None:
    """POST /assets/upload without 'file' field returns 422 (validation)."""
    response = await client.post("/api/v1/assets/upload", data={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_asset_empty_filename_400(client: AsyncClient) -> None:
    """POST /assets/upload with filename that is empty after strip returns 400."""
    files = {"file": ("   ", io.BytesIO(b"x"), "image/png")}
    response = await client.post("/api/v1/assets/upload", files=files)
    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_upload_asset_file_too_large_400(client: AsyncClient, mock_storage) -> None:
    """POST /assets/upload with file > MAX size returns 400."""
    app.dependency_overrides[_get_storage] = lambda: mock_storage
    try:
        over = MAX_UPLOAD_SIZE + 1
        files = {"file": ("big.png", io.BytesIO(b"x" * over), "image/png")}
        response = await client.post("/api/v1/assets/upload", files=files)
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "too large" in data["detail"].lower() or "large" in data["detail"].lower()
    finally:
        app.dependency_overrides.pop(_get_storage, None)


@pytest.mark.asyncio
async def test_upload_asset_disallowed_extension_400(client: AsyncClient) -> None:
    """POST /assets/upload with disallowed extension (e.g. .exe) returns 400."""
    files = {"file": ("script.exe", io.BytesIO(b"MZ"), "application/octet-stream")}
    response = await client.post("/api/v1/assets/upload", files=files)
    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_upload_asset_disallowed_content_type_400(client: AsyncClient) -> None:
    """POST /assets/upload with allowed extension but disallowed Content-Type returns 400."""
    files = {"file": ("image.png", io.BytesIO(b"\x89PNG"), "text/html")}
    response = await client.post("/api/v1/assets/upload", files=files)
    assert response.status_code == 400
    assert "detail" in response.json()
