"""Carousel business logic: create draft, update, build response with preview URL."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.enums import CarouselStatusEnum
from app.repositories.carousel_repository import CarouselRepository
from app.schemas.carousel import (
    CarouselCreate,
    CarouselListResponse,
    CarouselResponse,
    CarouselUpdate,
    FormatSchema,
)


def _format_to_dict(value: FormatSchema | None) -> dict:
    if value is None:
        return {}
    return value.model_dump(exclude_none=True)


def _carousel_to_response(carousel, preview_base_url: str) -> CarouselResponse:
    preview_url = f"{preview_base_url.rstrip('/')}/api/v1/carousels/{carousel.id}/preview"
    return CarouselResponse(
        id=carousel.id,
        title=carousel.title,
        source_type=carousel.source_type,
        source_payload=carousel.source_payload,
        format=carousel.format,
        status=carousel.status,
        language=carousel.language,
        slides_count=carousel.slides_count,
        created_at=carousel.created_at,
        updated_at=carousel.updated_at,
        preview_url=preview_url,
    )


class CarouselService:
    """Service for creating and updating carousels (draft), building API responses."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = CarouselRepository(session)
        self._preview_base_url = get_settings().PREVIEW_BASE_URL

    async def create_draft(self, payload: CarouselCreate) -> CarouselResponse:
        format_dict = _format_to_dict(payload.format)
        carousel = await self._repo.create(
            title=payload.title,
            source_type=payload.source_type,
            source_payload=payload.source_payload,
            format=format_dict,
            language=payload.language,
            slides_count=payload.slides_count,
        )
        return _carousel_to_response(carousel, self._preview_base_url)

    async def get_by_id(self, carousel_id: UUID) -> CarouselResponse | None:
        carousel = await self._repo.get_by_id(carousel_id)
        if carousel is None:
            return None
        return _carousel_to_response(carousel, self._preview_base_url)

    async def list(
        self,
        *,
        status: CarouselStatusEnum | None = None,
        lang: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> CarouselListResponse:
        carousels, total = await self._repo.list(
            status=status, lang=lang, skip=skip, limit=limit
        )
        items = [_carousel_to_response(c, self._preview_base_url) for c in carousels]
        return CarouselListResponse(items=items, total=total)

    async def update(
        self,
        carousel_id: UUID,
        payload: CarouselUpdate,
    ) -> CarouselResponse | None:
        carousel = await self._repo.get_by_id(carousel_id)
        if carousel is None:
            return None
        format_dict = _format_to_dict(payload.format) if payload.format is not None else None
        updated = await self._repo.update(
            carousel,
            title=payload.title,
            format=format_dict,
        )
        return _carousel_to_response(updated, self._preview_base_url)
