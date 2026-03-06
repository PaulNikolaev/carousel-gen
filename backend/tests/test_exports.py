"""Pytest + httpx tests for /api/v1/exports: POST start export, GET export by id, GET stream SSE."""

import json
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.exports import _get_storage
from app.main import app
from app.models.enums import ExportStatusEnum
from app.repositories.export_repository import ExportRepository


class MockStorageService:
    """Mock StorageService: generate_presigned_url returns fixed URL without S3."""

    async def generate_presigned_url(
        self,
        key: str,
        bucket: str | None = None,
        expires_in: int = 3600,
    ) -> str:
        return f"https://mock.example/download/{key}"


@pytest.fixture
async def client_with_mock_storage(client: AsyncClient):
    """Client with StorageService overridden so GET export (done) does not hit S3."""
    mock_storage = MockStorageService()
    app.dependency_overrides[_get_storage] = lambda: mock_storage
    try:
        yield client
    finally:
        app.dependency_overrides.pop(_get_storage, None)


async def test_post_export_202(client: AsyncClient) -> None:
    """POST /exports with valid carousel_id returns 202 and export_id."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Export Carousel", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]

    response = await client.post(
        "/api/v1/exports",
        json={"carousel_id": carousel_id},
    )
    assert response.status_code == 202
    data = response.json()
    assert "export_id" in data
    assert data["export_id"] is not None


async def test_post_export_carousel_not_found_404(client: AsyncClient) -> None:
    """POST /exports with non-existent carousel_id returns 404."""
    fake_carousel_id = "00000000-0000-0000-0000-000000000001"
    response = await client.post(
        "/api/v1/exports",
        json={"carousel_id": fake_carousel_id},
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "carousel" in data["detail"].lower() or "not found" in data["detail"].lower()


async def test_get_export_200(
    client_and_session: tuple[AsyncClient, AsyncSession],
) -> None:
    """GET /exports/{id} returns 200 with status and export shape."""
    client, session = client_and_session
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Get Export Carousel", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]

    export_repo = ExportRepository(session)
    export = await export_repo.create(
        carousel_id=UUID(carousel_id) if isinstance(carousel_id, str) else carousel_id
    )
    await session.flush()
    export_id = str(export.id)

    response = await client.get(f"/api/v1/exports/{export_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == export_id
    assert data["carousel_id"] == carousel_id
    assert data["status"] in ("pending", "running", "done", "failed")
    assert "created_at" in data
    assert "updated_at" in data
    assert "error_message" in data


async def test_get_export_not_found_404(client: AsyncClient) -> None:
    """GET /exports/{id} returns 404 for non-existent export."""
    fake_export_id = "00000000-0000-0000-0000-000000000002"
    response = await client.get(f"/api/v1/exports/{fake_export_id}")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "export" in data["detail"].lower() or "not found" in data["detail"].lower()


async def test_get_export_done_has_download_url(
    client_and_session: tuple[AsyncClient, AsyncSession],
) -> None:
    """GET /exports/{id} when status=done returns download_url (presigned)."""
    client, session = client_and_session
    app.dependency_overrides[_get_storage] = lambda: MockStorageService()
    try:
        create_resp = await client.post(
            "/api/v1/carousels",
            json={"title": "Done Export Carousel", "source_type": "text"},
        )
        assert create_resp.status_code == 201
        carousel_id = create_resp.json()["id"]

        export_repo = ExportRepository(session)
        export = await export_repo.create(
            carousel_id=UUID(carousel_id) if isinstance(carousel_id, str) else carousel_id
        )
        await export_repo.update(
            export,
            status=ExportStatusEnum.done,
            s3_key="exports/fake/archive.zip",
        )
        await session.flush()
        export_id = str(export.id)

        response = await client.get(f"/api/v1/exports/{export_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert data["download_url"] is not None
        assert "mock.example" in data["download_url"] or "download" in data["download_url"]
    finally:
        app.dependency_overrides.pop(_get_storage, None)


async def test_post_export_invalid_carousel_id_422(client: AsyncClient) -> None:
    """POST /exports with invalid carousel_id (not UUID) returns 422."""
    response = await client.post(
        "/api/v1/exports",
        json={"carousel_id": "not-a-uuid"},
    )
    assert response.status_code == 422


async def test_post_export_missing_carousel_id_422(client: AsyncClient) -> None:
    """POST /exports without carousel_id returns 422."""
    response = await client.post("/api/v1/exports", json={})
    assert response.status_code == 422


async def test_get_export_stream_404(client: AsyncClient) -> None:
    """GET /exports/{id}/stream returns 404 for non-existent export."""
    response = await client.get(
        "/api/v1/exports/00000000-0000-0000-0000-000000000002/stream"
    )
    assert response.status_code == 404


async def test_get_export_stream_200_sends_events(
    client_and_session: tuple[AsyncClient, AsyncSession],
) -> None:
    """GET /exports/{id}/stream returns 200 and sends at least one SSE event until done/failed."""
    client, session = client_and_session
    app.dependency_overrides[_get_storage] = lambda: MockStorageService()
    try:
        create_resp = await client.post(
            "/api/v1/carousels",
            json={"title": "Stream Export Carousel", "source_type": "text"},
        )
        assert create_resp.status_code == 201
        carousel_id = create_resp.json()["id"]

        export_repo = ExportRepository(session)
        export = await export_repo.create(
            carousel_id=UUID(carousel_id) if isinstance(carousel_id, str) else carousel_id
        )
        await export_repo.update(
            export,
            status=ExportStatusEnum.done,
            s3_key="exports/fake/archive.zip",
        )
        await session.flush()
        export_id = str(export.id)

        async with client.stream(
            "GET", f"/api/v1/exports/{export_id}/stream"
        ) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")
            lines = []
            async for line in response.aiter_lines():
                lines.append(line)
                if line.startswith("data: "):
                    payload = json.loads(line[6:])
                    if payload.get("status") in ("done", "failed"):
                        break

        data_lines = [ln for ln in lines if ln.startswith("data: ")]
        assert len(data_lines) >= 1
        first = json.loads(data_lines[0][6:])
        assert first["id"] == export_id
        assert first["carousel_id"] == carousel_id
        assert first["status"] in ("pending", "running", "done", "failed")
        assert "created_at" in first
        if first["status"] == "done":
            assert "download_url" in first
    finally:
        app.dependency_overrides.pop(_get_storage, None)
