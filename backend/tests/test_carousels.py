"""Pytest + httpx tests for /api/v1/carousels: POST, GET list, GET by id, PATCH."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_carousel_201(client: AsyncClient) -> None:
    """POST /carousels — valid payload returns 201 and carousel shape."""
    response = await client.post(
        "/api/v1/carousels",
        json={
            "title": "Test Carousel",
            "source_type": "text",
            "source_payload": {},
            "format": {"slides_count": 5, "language": "ru"},
            "language": "ru",
            "slides_count": 5,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Carousel"
    assert data["source_type"] == "text"
    assert data["status"] == "draft"
    assert data["language"] == "ru"
    assert data["slides_count"] == 5
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "preview_url" in data
    assert "/api/v1/carousels/" in data["preview_url"] and "/preview" in data["preview_url"]


@pytest.mark.asyncio
async def test_create_carousel_minimal_payload_201(client: AsyncClient) -> None:
    """POST /carousels with minimal/default payload returns 201."""
    response = await client.post("/api/v1/carousels", json={})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == ""
    assert data["source_type"] == "text"
    assert data["status"] == "draft"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_carousel_invalid_source_type_422(client: AsyncClient) -> None:
    """POST /carousels with invalid source_type returns 422."""
    response = await client.post(
        "/api/v1/carousels",
        json={"source_type": "invalid_enum"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_carousels_empty_200(client: AsyncClient) -> None:
    """GET /carousels returns 200 and items/total."""
    response = await client.get("/api/v1/carousels")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_list_carousels_with_filters_200(client: AsyncClient) -> None:
    """GET /carousels?status=draft&lang=ru returns 200."""
    response = await client.get("/api/v1/carousels?status=draft&lang=ru")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_carousels_after_create_200(client: AsyncClient) -> None:
    """Create one carousel, then GET list — total 1, item shape."""
    await client.post(
        "/api/v1/carousels",
        json={"title": "List Test", "source_type": "text", "language": "en"},
    )
    response = await client.get("/api/v1/carousels")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "List Test"
    assert data["items"][0]["language"] == "en"


@pytest.mark.asyncio
async def test_get_carousel_200(client: AsyncClient) -> None:
    """GET /carousels/{id} returns 200 for existing carousel."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Get Me", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/carousels/{carousel_id}")
    assert response.status_code == 200
    assert response.json()["id"] == carousel_id
    assert response.json()["title"] == "Get Me"


@pytest.mark.asyncio
async def test_get_carousel_not_found_404(client: AsyncClient) -> None:
    """GET /carousels/{id} returns 404 for non-existent UUID."""
    response = await client.get(
        "/api/v1/carousels/00000000-0000-0000-0000-000000000001"
    )
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_patch_carousel_200(client: AsyncClient) -> None:
    """PATCH /carousels/{id} updates title/format and returns 200."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Original", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    response = await client.patch(
        f"/api/v1/carousels/{carousel_id}",
        json={"title": "Updated Title", "format": {"slides_count": 10}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["format"].get("slides_count") == 10


@pytest.mark.asyncio
async def test_patch_carousel_not_found_404(client: AsyncClient) -> None:
    """PATCH /carousels/{id} returns 404 for non-existent UUID."""
    response = await client.patch(
        "/api/v1/carousels/00000000-0000-0000-0000-000000000001",
        json={"title": "No"},
    )
    assert response.status_code == 404
    assert "detail" in response.json()
