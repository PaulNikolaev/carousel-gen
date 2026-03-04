"""Pytest + httpx tests for /api/v1/carousels/{id}/slides: GET list, PATCH slide."""

from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slide import Slide


@pytest.mark.asyncio
async def test_get_slides_carousel_not_found_404(client: AsyncClient) -> None:
    """GET /carousels/{id}/slides returns 404 when carousel does not exist."""
    response = await client.get(
        "/api/v1/carousels/00000000-0000-0000-0000-000000000001/slides"
    )
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_slides_empty_list_200(client: AsyncClient) -> None:
    """Create carousel (no slides), GET slides → 200 and empty list."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Empty", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/carousels/{carousel_id}/slides")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_slides_ordered_200(
    client_and_session: tuple[AsyncClient, AsyncSession],
) -> None:
    """Create carousel, add two slides via repo, GET slides → 200 and list ordered by order."""
    client, session = client_and_session
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "With Slides", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    cid = UUID(carousel_id) if isinstance(carousel_id, str) else carousel_id

    s1 = Slide(carousel_id=cid, order=1, title="First", body="", footer="")
    s2 = Slide(carousel_id=cid, order=0, title="Zeroth", body="b", footer="")
    session.add_all([s1, s2])
    await session.flush()

    response = await client.get(f"/api/v1/carousels/{carousel_id}/slides")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["order"] == 0 and data[0]["title"] == "Zeroth"
    assert data[1]["order"] == 1 and data[1]["title"] == "First"


@pytest.mark.asyncio
async def test_patch_slide_200(
    client_and_session: tuple[AsyncClient, AsyncSession],
) -> None:
    """Create carousel, add slide via repo, PATCH slide → 200 and updated fields."""
    client, session = client_and_session
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Patch Test", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    cid = UUID(carousel_id) if isinstance(carousel_id, str) else carousel_id

    slide = Slide(
        carousel_id=cid,
        order=0,
        title="Old",
        body="Body",
        footer="Foot",
    )
    session.add(slide)
    await session.flush()
    await session.refresh(slide)
    slide_id = slide.id

    response = await client.patch(
        f"/api/v1/carousels/{carousel_id}/slides/{slide_id}",
        json={"title": "New Title", "body": "New body", "footer": "New footer"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(slide_id)
    assert data["carousel_id"] == str(carousel_id)
    assert data["title"] == "New Title"
    assert data["body"] == "New body"
    assert data["footer"] == "New footer"


@pytest.mark.asyncio
async def test_patch_slide_not_found_404(client: AsyncClient) -> None:
    """PATCH /carousels/{id}/slides/{slide_id} returns 404 when slide does not exist."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Carousel", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    fake_slide_id = uuid4()

    response = await client.patch(
        f"/api/v1/carousels/{carousel_id}/slides/{fake_slide_id}",
        json={"title": "Any"},
    )
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_patch_slide_carousel_not_found_404(client: AsyncClient) -> None:
    """PATCH with non-existent carousel_id returns 404."""
    fake_carousel_id = "00000000-0000-0000-0000-000000000001"
    fake_slide_id = uuid4()
    response = await client.patch(
        f"/api/v1/carousels/{fake_carousel_id}/slides/{fake_slide_id}",
        json={"title": "Any"},
    )
    assert response.status_code == 404
    assert "detail" in response.json()
