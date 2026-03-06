"""Pytest + httpx tests for /api/v1/carousels: POST, GET list, GET by id, PATCH, video upload, video_url."""

import io
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.carousels import _get_storage
from app.main import app
from app.models.slide import Slide


class MockStorageService:
    """Mock StorageService for tests; upload_file returns a fixed key without S3."""

    async def upload_file(self, file_obj, filename, bucket=None, prefix="uploads"):
        return "http://mock/url", f"{prefix}/mock-{filename}"


@pytest.fixture
async def client_with_mock_storage(client: AsyncClient):
    """Client with StorageService overridden so uploads don't hit S3."""
    mock_storage = MockStorageService()
    app.dependency_overrides[_get_storage] = lambda: mock_storage
    try:
        yield client
    finally:
        app.dependency_overrides.pop(_get_storage, None)


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


async def test_create_carousel_minimal_payload_201(client: AsyncClient) -> None:
    """POST /carousels with minimal/default payload returns 201."""
    response = await client.post("/api/v1/carousels", json={})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == ""
    assert data["source_type"] == "text"
    assert data["status"] == "draft"
    assert "id" in data


async def test_create_carousel_invalid_source_type_422(client: AsyncClient) -> None:
    """POST /carousels with invalid source_type returns 422."""
    response = await client.post(
        "/api/v1/carousels",
        json={"source_type": "invalid_enum"},
    )
    assert response.status_code == 422


async def test_list_carousels_empty_200(client: AsyncClient) -> None:
    """GET /carousels returns 200 and items/total."""
    response = await client.get("/api/v1/carousels")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 0
    assert data["items"] == []


async def test_list_carousels_with_filters_200(client: AsyncClient) -> None:
    """GET /carousels?status=draft&lang=ru returns 200."""
    response = await client.get("/api/v1/carousels?status=draft&lang=ru")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


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


async def test_get_carousel_not_found_404(client: AsyncClient) -> None:
    """GET /carousels/{id} returns 404 for non-existent UUID."""
    response = await client.get(
        "/api/v1/carousels/00000000-0000-0000-0000-000000000001"
    )
    assert response.status_code == 404
    assert "detail" in response.json()


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


async def test_patch_carousel_not_found_404(client: AsyncClient) -> None:
    """PATCH /carousels/{id} returns 404 for non-existent UUID."""
    response = await client.patch(
        "/api/v1/carousels/00000000-0000-0000-0000-000000000001",
        json={"title": "No"},
    )
    assert response.status_code == 404
    assert "detail" in response.json()


# --- POST /carousels/{id}/video (step 4.2) ---


async def test_upload_carousel_video_200(client_with_mock_storage: AsyncClient) -> None:
    """POST /carousels/{id}/video with valid mp4 returns 200 and source_payload.video_key."""
    create_resp = await client_with_mock_storage.post(
        "/api/v1/carousels",
        json={"title": "Video Carousel", "source_type": "video"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    response = await client_with_mock_storage.post(
        f"/api/v1/carousels/{carousel_id}/video",
        files={"file": ("test.mp4", io.BytesIO(b"fake mp4 content"), "video/mp4")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source_type"] == "video"
    assert "source_payload" in data
    assert data["source_payload"].get("video_key") is not None
    assert "carousels/video" in data["source_payload"]["video_key"] or "mock" in data["source_payload"]["video_key"]


async def test_upload_carousel_video_wrong_source_type_400(
    client_with_mock_storage: AsyncClient,
) -> None:
    """POST /carousels/{id}/video for carousel with source_type != video returns 400."""
    create_resp = await client_with_mock_storage.post(
        "/api/v1/carousels",
        json={"title": "Text Carousel", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    response = await client_with_mock_storage.post(
        f"/api/v1/carousels/{carousel_id}/video",
        files={"file": ("test.mp4", io.BytesIO(b"x"), "video/mp4")},
    )
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "video" in response.json()["detail"].lower()


async def test_upload_carousel_video_not_found_404(
    client_with_mock_storage: AsyncClient,
) -> None:
    """POST /carousels/{id}/video for non-existent carousel returns 404."""
    response = await client_with_mock_storage.post(
        "/api/v1/carousels/00000000-0000-0000-0000-000000000001/video",
        files={"file": ("test.mp4", io.BytesIO(b"x"), "video/mp4")},
    )
    assert response.status_code == 404
    assert "detail" in response.json()


async def test_upload_carousel_video_invalid_file_type_400(
    client_with_mock_storage: AsyncClient,
) -> None:
    """POST /carousels/{id}/video with wrong extension/content-type returns 400."""
    create_resp = await client_with_mock_storage.post(
        "/api/v1/carousels",
        json={"title": "Video Carousel", "source_type": "video"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    response = await client_with_mock_storage.post(
        f"/api/v1/carousels/{carousel_id}/video",
        files={"file": ("document.pdf", io.BytesIO(b"pdf"), "application/pdf")},
    )
    assert response.status_code == 400
    assert "detail" in response.json()


async def test_upload_carousel_video_file_too_large_400(
    client_with_mock_storage: AsyncClient,
) -> None:
    """POST /carousels/{id}/video with file > 50 MB returns 400."""
    create_resp = await client_with_mock_storage.post(
        "/api/v1/carousels",
        json={"title": "Video Carousel", "source_type": "video"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    # 50 * 1024 * 1024 + 1 byte
    big = io.BytesIO(b"x" * (50 * 1024 * 1024 + 1))
    response = await client_with_mock_storage.post(
        f"/api/v1/carousels/{carousel_id}/video",
        files={"file": ("large.mp4", big, "video/mp4")},
    )
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "50" in response.json()["detail"] or "large" in response.json()["detail"].lower()


# --- PATCH /carousels/{id} with video_url (step 4.2) ---


async def test_patch_carousel_video_url_200(client: AsyncClient) -> None:
    """PATCH /carousels/{id} with video_url for video carousel returns 200 and source_payload.video_url."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Video Carousel", "source_type": "video"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    response = await client.patch(
        f"/api/v1/carousels/{carousel_id}",
        json={"video_url": "https://example.com/v.mp4"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source_type"] == "video"
    assert data["source_payload"].get("video_url") == "https://example.com/v.mp4"


async def test_patch_carousel_video_url_invalid_url_422(client: AsyncClient) -> None:
    """PATCH /carousels/{id} with invalid video_url (non http/https) returns 422."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Video Carousel", "source_type": "video"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    response = await client.patch(
        f"/api/v1/carousels/{carousel_id}",
        json={"video_url": "ftp://example.com/v.mp4"},
    )
    assert response.status_code == 422


async def test_patch_carousel_video_url_non_video_400(client: AsyncClient) -> None:
    """PATCH /carousels/{id} with video_url for non-video carousel returns 400."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Text Carousel", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    response = await client.patch(
        f"/api/v1/carousels/{carousel_id}",
        json={"video_url": "https://example.com/v.mp4"},
    )
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "video" in response.json()["detail"].lower()


async def test_patch_carousel_video_url_not_found_404(client: AsyncClient) -> None:
    """PATCH /carousels/{id} with video_url for non-existent carousel returns 404."""
    response = await client.patch(
        "/api/v1/carousels/00000000-0000-0000-0000-000000000001",
        json={"video_url": "https://example.com/v.mp4"},
    )
    assert response.status_code == 404
    assert "detail" in response.json()


# --- GET /carousels/{id}/design (step 7.3) ---


async def test_get_carousel_design_200(client: AsyncClient) -> None:
    """GET /carousels/{id}/design returns 200 and design snapshot (get-or-create)."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Get Design", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/carousels/{carousel_id}/design")
    assert response.status_code == 200
    data = response.json()
    assert "design" in data
    design = data["design"]
    assert "template" in design
    assert "background_type" in design
    assert "padding" in design
    assert "header_enabled" in design
    assert "footer_enabled" in design


async def test_get_carousel_design_not_found_404(client: AsyncClient) -> None:
    """GET /carousels/{id}/design returns 404 for non-existent carousel."""
    response = await client.get(
        "/api/v1/carousels/00000000-0000-0000-0000-000000000001/design"
    )
    assert response.status_code == 404
    assert "detail" in response.json()


async def test_get_carousel_design_with_slide_id_200(
    client_and_session: tuple[AsyncClient, AsyncSession],
) -> None:
    """GET /carousels/{id}/design?slide_id=... returns 200 and effective design for that slide (overrides merged)."""
    client, session = client_and_session
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Design Slide", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    cid = UUID(carousel_id) if isinstance(carousel_id, str) else carousel_id

    slide = Slide(
        carousel_id=cid,
        order=0,
        title="S1",
        body="",
        footer="",
        design_overrides={"padding": 16, "header_text": "Slide header"},
    )
    session.add(slide)
    await session.flush()
    await session.refresh(slide)
    slide_id = str(slide.id)

    response = await client.get(
        f"/api/v1/carousels/{carousel_id}/design",
        params={"slide_id": slide_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert "design" in data
    assert data["design"]["padding"] == 16
    assert data["design"]["header_text"] == "Slide header"


async def test_get_carousel_design_slide_not_found_404(client: AsyncClient) -> None:
    """GET /carousels/{id}/design?slide_id=<non_existent> returns 404."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Design", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    response = await client.get(
        f"/api/v1/carousels/{carousel_id}/design",
        params={"slide_id": "00000000-0000-0000-0000-000000000099"},
    )
    assert response.status_code == 404
    assert "detail" in response.json()


# --- PATCH /carousels/{id}/design (step 4.3) ---


async def test_patch_carousel_design_partial_200(client: AsyncClient) -> None:
    """PATCH /carousels/{id}/design with partial payload returns 200 and design snapshot."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Design Test", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/carousels/{carousel_id}/design",
        json={
            "template": "bold",
            "header": {"enabled": True, "text": "My Header"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "design" in data
    design = data["design"]
    assert design["template"] == "bold"
    assert design["header_enabled"] is True
    assert design["header_text"] == "My Header"
    assert "background_type" in design
    assert "padding" in design
    assert "footer_enabled" in design
    assert data["id"] == carousel_id
    assert data["title"] == "Design Test"


async def test_patch_carousel_design_apply_to_all_resets_overrides(
    client_and_session: tuple[AsyncClient, AsyncSession],
) -> None:
    """PATCH .../design?apply_to_all=true resets design_overrides on all slides to {}."""
    client, session = client_and_session
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Apply To All", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    cid = UUID(carousel_id) if isinstance(carousel_id, str) else carousel_id

    slide = Slide(
        carousel_id=cid,
        order=0,
        title="S1",
        body="",
        footer="",
        design_overrides={"padding": 10},
    )
    session.add(slide)
    await session.flush()
    await session.refresh(slide)

    response = await client.patch(
        f"/api/v1/carousels/{carousel_id}/design",
        params={"apply_to_all": True},
        json={"template": "minimal"},
    )
    assert response.status_code == 200
    assert response.json()["design"]["template"] == "minimal"

    slides_resp = await client.get(f"/api/v1/carousels/{carousel_id}/slides")
    assert slides_resp.status_code == 200
    slides = slides_resp.json()
    assert len(slides) == 1
    assert slides[0]["design_overrides"] == {}


async def test_patch_carousel_design_not_found_404(client: AsyncClient) -> None:
    """PATCH /carousels/{id}/design returns 404 for non-existent carousel_id."""
    response = await client.patch(
        "/api/v1/carousels/00000000-0000-0000-0000-000000000001/design",
        json={"template": "bold"},
    )
    assert response.status_code == 404
    assert "detail" in response.json()


async def test_patch_carousel_design_typography_200(client: AsyncClient) -> None:
    """PATCH /carousels/{id}/design with typography returns 200 and design includes typography fields."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Typography Design", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/carousels/{carousel_id}/design",
        json={
            "typography": {
                "font_size": 20,
                "font_family": "Arial",
                "font_weight": "bold",
                "font_style": "italic",
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "design" in data
    design = data["design"]
    assert design["font_size"] == 20
    assert design["font_family"] == "Arial"
    assert design["font_weight"] == "bold"
    assert design["font_style"] == "italic"


async def test_patch_carousel_design_with_slide_id_200(
    client_and_session: tuple[AsyncClient, AsyncSession],
) -> None:
    """PATCH /carousels/{id}/design?slide_id=... updates only that slide's design_overrides."""
    client, session = client_and_session
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Slide Design PATCH", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    cid = UUID(carousel_id) if isinstance(carousel_id, str) else carousel_id

    slide1 = Slide(
        carousel_id=cid,
        order=0,
        title="S1",
        body="",
        footer="",
        design_overrides={},
    )
    slide2 = Slide(
        carousel_id=cid,
        order=1,
        title="S2",
        body="",
        footer="",
        design_overrides={},
    )
    session.add_all([slide1, slide2])
    await session.flush()
    await session.refresh(slide1)
    slide_id = str(slide1.id)

    response = await client.patch(
        f"/api/v1/carousels/{carousel_id}/design",
        params={"slide_id": slide_id},
        json={"template": "minimal", "header": {"enabled": False}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["design"]["template"] == "minimal"
    assert data["design"]["header_enabled"] is False

    slides_resp = await client.get(f"/api/v1/carousels/{carousel_id}/slides")
    assert slides_resp.status_code == 200
    slides = {s["id"]: s for s in slides_resp.json()}
    assert slides[slide_id]["design_overrides"] != {}
    assert slides[slide_id]["design_overrides"].get("template") == "minimal"
    other_slide = next(s for sid, s in slides.items() if sid != slide_id)
    assert other_slide["design_overrides"] == {}


async def test_patch_carousel_design_slide_id_not_found_404(
    client: AsyncClient,
) -> None:
    """PATCH /carousels/{id}/design?slide_id=<non_existent> returns 404."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Design", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    response = await client.patch(
        f"/api/v1/carousels/{carousel_id}/design",
        params={"slide_id": "00000000-0000-0000-0000-000000000099"},
        json={"template": "bold"},
    )
    assert response.status_code == 404
    assert "detail" in response.json()


async def test_list_carousel_generations_empty_200(client: AsyncClient) -> None:
    """GET /carousels/{id}/generations returns 200 and empty items for new carousel."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Gen History", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/carousels/{carousel_id}/generations")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["items"] == []


async def test_list_carousel_generations_after_start_200(client: AsyncClient) -> None:
    """GET /carousels/{id}/generations returns items with id, created_at, status, tokens_used after start."""
    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Gen History", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = create_resp.json()["id"]
    start_resp = await client.post(
        "/api/v1/generations",
        json={"carousel_id": carousel_id},
    )
    assert start_resp.status_code == 202
    response = await client.get(f"/api/v1/carousels/{carousel_id}/generations")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    item = data["items"][0]
    assert "id" in item
    assert "created_at" in item
    assert "status" in item
    assert item["status"] in ("queued", "running", "done", "failed")
    assert "tokens_used" in item


async def test_list_carousel_generations_not_found_404(client: AsyncClient) -> None:
    """GET /carousels/{id}/generations returns 404 for non-existent carousel."""
    response = await client.get(
        f"/api/v1/carousels/{uuid4()}/generations",
    )
    assert response.status_code == 404
    assert "detail" in response.json()


async def test_list_carousel_generations_order_desc(
    client_and_session: tuple[AsyncClient, AsyncSession],
) -> None:
    """GET /carousels/{id}/generations returns items ordered by created_at DESC."""
    from uuid import UUID

    from app.repositories.carousel_repository import CarouselRepository
    from app.repositories.generation_repository import GenerationRepository

    client, session = client_and_session
    carousel_repo = CarouselRepository(session)
    gen_repo = GenerationRepository(session)

    create_resp = await client.post(
        "/api/v1/carousels",
        json={"title": "Order Test", "source_type": "text"},
    )
    assert create_resp.status_code == 201
    carousel_id = UUID(create_resp.json()["id"])
    carousel = await carousel_repo.get_by_id(carousel_id)
    assert carousel is not None

    gen1 = await gen_repo.create(carousel_id=carousel_id, tokens_estimate=0)
    await session.flush()
    gen2 = await gen_repo.create(carousel_id=carousel_id, tokens_estimate=0)
    await session.flush()

    response = await client.get(f"/api/v1/carousels/{carousel_id}/generations")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 2
    # Order by created_at DESC (when equal, order may be non-deterministic)
    assert items[0]["created_at"] >= items[1]["created_at"]
    ids = {item["id"] for item in items}
    assert ids == {str(gen1.id), str(gen2.id)}
