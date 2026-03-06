"""Pytest + httpx tests for /api/v1/generations: POST start, GET by id, GET stream SSE."""

import json
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import CarouselStatusEnum, GenerationStatusEnum
from app.repositories.carousel_repository import CarouselRepository
from app.repositories.generation_repository import GenerationRepository


@pytest.fixture
async def draft_carousel_id(client: AsyncClient) -> str:
    """Create a draft carousel via API and return its id (for happy path tests)."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Gen Test", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    return create_resp.json()["id"]


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
    assert data["tokens_estimate"] == -1  # reserved: pre-run token count not implemented
    assert data["generation_id"] != draft_carousel_id


async def test_start_generation_202_carousel_becomes_generating(
    client: AsyncClient, draft_carousel_id: str
) -> None:
    """POST /generations with valid carousel_id: after 202, carousel status becomes 'generating'."""
    response = await client.post(
        "/api/v1/generations",
        json={"carousel_id": draft_carousel_id},
    )
    assert response.status_code == 202
    carousel_resp = await client.get(f"/api/v1/carousels/{draft_carousel_id}")
    assert carousel_resp.status_code == 200
    assert carousel_resp.json()["status"] == "generating"


async def test_start_generation_when_ready_202(
    client_and_session: tuple[AsyncClient, AsyncSession],
) -> None:
    """POST /generations when carousel status is 'ready' returns 202, carousel becomes 'generating'."""
    client, session = client_and_session
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Ready Carousel", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    cid = UUID(carousel_id)
    carousel_repo = CarouselRepository(session)
    carousel = await carousel_repo.get_by_id(cid)
    assert carousel is not None
    await carousel_repo.update(carousel, status=CarouselStatusEnum.ready)
    await session.flush()

    response = await client.post(
        "/api/v1/generations",
        json={"carousel_id": carousel_id},
    )
    assert response.status_code == 202
    assert "generation_id" in response.json()
    carousel_resp = await client.get(f"/api/v1/carousels/{carousel_id}")
    assert carousel_resp.status_code == 200
    assert carousel_resp.json()["status"] == "generating"


async def test_start_generation_when_failed_202(
    client_and_session: tuple[AsyncClient, AsyncSession],
) -> None:
    """POST /generations when carousel status is 'failed' returns 202, carousel becomes 'generating'."""
    client, session = client_and_session
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Failed Carousel", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    cid = UUID(carousel_id)
    carousel_repo = CarouselRepository(session)
    carousel = await carousel_repo.get_by_id(cid)
    assert carousel is not None
    await carousel_repo.update(carousel, status=CarouselStatusEnum.failed)
    await session.flush()

    response = await client.post(
        "/api/v1/generations",
        json={"carousel_id": carousel_id},
    )
    assert response.status_code == 202
    assert "generation_id" in response.json()
    carousel_resp = await client.get(f"/api/v1/carousels/{carousel_id}")
    assert carousel_resp.status_code == 200
    assert carousel_resp.json()["status"] == "generating"


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


async def test_start_generation_invalid_body_422(client: AsyncClient) -> None:
    """POST /generations with missing carousel_id returns 422."""
    response = await client.post("/api/v1/generations", json={})
    assert response.status_code == 422


async def test_start_generation_invalid_uuid_422(client: AsyncClient) -> None:
    """POST /generations with invalid UUID format returns 422."""
    response = await client.post(
        "/api/v1/generations",
        json={"carousel_id": "not-a-uuid"},
    )
    assert response.status_code == 422


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


async def test_get_generation_not_found_404(client: AsyncClient) -> None:
    """GET /generations/{id} returns 404 for non-existent generation."""
    response = await client.get(
        "/api/v1/generations/00000000-0000-0000-0000-000000000001"
    )
    assert response.status_code == 404
    assert "detail" in response.json()


async def test_get_generation_invalid_uuid_404(client: AsyncClient) -> None:
    """GET /generations/{id} with non-UUID path does not match route; FastAPI returns 404."""
    response = await client.get("/api/v1/generations/not-a-uuid")
    assert response.status_code == 404


async def test_get_generation_stream_404(client: AsyncClient) -> None:
    """GET /generations/{id}/stream returns 404 for non-existent generation."""
    response = await client.get(
        "/api/v1/generations/00000000-0000-0000-0000-000000000001/stream"
    )
    assert response.status_code == 404


async def test_get_generation_stream_200_sends_events(
    client_and_session: tuple[AsyncClient, AsyncSession],
) -> None:
    """GET /generations/{id}/stream returns 200 and sends at least one SSE event until done/failed."""
    client, session = client_and_session
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Stream Gen", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]

    gen_repo = GenerationRepository(session)
    carousel_repo = CarouselRepository(session)
    carousel = await carousel_repo.get_by_id(UUID(carousel_id))
    assert carousel is not None
    gen = await gen_repo.create(carousel_id=carousel.id, tokens_estimate=100)
    await gen_repo.update(gen, status=GenerationStatusEnum.done, tokens_used=50)
    await session.flush()
    generation_id = str(gen.id)

    async with client.stream(
        "GET", f"/api/v1/generations/{generation_id}/stream"
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
    assert first["id"] == generation_id
    assert first["carousel_id"] == carousel_id
    assert first["status"] in ("queued", "running", "done", "failed")
    assert "tokens_estimate" in first
    assert "created_at" in first
