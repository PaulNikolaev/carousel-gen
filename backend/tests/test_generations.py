"""Pytest + httpx tests for /api/v1/generations: POST start, GET by id."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.fixture
async def draft_carousel_id(client: AsyncClient) -> str:
    """Create a draft carousel via API and return its id (for happy path tests)."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Gen Test", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    return create_resp.json()["id"]


@pytest.mark.asyncio
async def test_start_generation_202(client: AsyncClient, draft_carousel_id: str) -> None:
    """POST /generations with valid draft carousel_id returns 202 and generation_id, tokens_estimate."""
    response = await client.post(
        "/api/v1/generations",
        json={"carousel_id": draft_carousel_id},
    )
    assert response.status_code == 202
    data = response.json()
    assert "generation_id" in data
    assert "tokens_estimate" in data
    assert data["tokens_estimate"] >= 0
    assert data["generation_id"] != draft_carousel_id


@pytest.mark.asyncio
async def test_start_generation_carousel_not_found_404(client: AsyncClient) -> None:
    """POST /generations with non-existent carousel_id returns 404 (CarouselNotFoundError)."""
    response = await client.post(
        "/api/v1/generations",
        json={"carousel_id": str(uuid4())},
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_start_generation_carousel_conflict_409(client: AsyncClient) -> None:
    """POST /generations when carousel is not draft or has active generation returns 409 (CarouselConflictError)."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Draft", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    # Start generation once → carousel becomes 'generating', active generation exists
    await client.post("/api/v1/generations", json={"carousel_id": carousel_id})
    # Second start for same carousel → 409
    response = await client.post(
        "/api/v1/generations",
        json={"carousel_id": carousel_id},
    )
    assert response.status_code == 409
    data = response.json()
    assert "detail" in data
    assert "draft" in data["detail"].lower() or "active" in data["detail"].lower()


@pytest.mark.asyncio
async def test_start_generation_invalid_body_422(client: AsyncClient) -> None:
    """POST /generations with missing carousel_id returns 422."""
    response = await client.post("/api/v1/generations", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_start_generation_invalid_uuid_422(client: AsyncClient) -> None:
    """POST /generations with invalid UUID format returns 422."""
    response = await client.post(
        "/api/v1/generations",
        json={"carousel_id": "not-a-uuid"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_generation_200(client: AsyncClient) -> None:
    """GET /generations/{id} returns 200 with full generation payload."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Get Gen", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    start_resp = await client.post(
        "/api/v1/generations",
        json={"carousel_id": carousel_id},
    )
    assert start_resp.status_code == 202
    generation_id = start_resp.json()["generation_id"]

    response = await client.get(f"/api/v1/generations/{generation_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == generation_id
    assert data["carousel_id"] == carousel_id
    assert "status" in data
    assert data["status"] in ("queued", "running", "done", "failed")
    assert "tokens_estimate" in data
    assert "tokens_used" in data
    assert "result" in data
    assert "error_message" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_get_generation_not_found_404(client: AsyncClient) -> None:
    """GET /generations/{id} returns 404 for non-existent generation."""
    response = await client.get(
        "/api/v1/generations/00000000-0000-0000-0000-000000000001"
    )
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_generation_invalid_uuid_404(client: AsyncClient) -> None:
    """GET /generations/{id} with non-UUID path does not match route; FastAPI returns 404."""
    response = await client.get("/api/v1/generations/not-a-uuid")
    assert response.status_code == 404
