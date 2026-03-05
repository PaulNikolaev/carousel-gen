"""Carousel business logic: create draft, update, build response with preview URL."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.enums import CarouselStatusEnum, SourceTypeEnum
from app.repositories.carousel_repository import CarouselRepository
from app.schemas.carousel import (
    CarouselCreate,
    CarouselListResponse,
    CarouselResponse,
    CarouselUpdate,
    FormatSchema,
)
from app.services.response_utils import carousel_to_response


def _format_to_dict(value: FormatSchema | None) -> dict:
    if value is None:
        return {}
    return value.model_dump(exclude_none=True)


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
        return carousel_to_response(carousel, self._preview_base_url)

    async def get_by_id(self, carousel_id: UUID) -> CarouselResponse | None:
        carousel = await self._repo.get_by_id(carousel_id)
        if carousel is None:
            return None
        return carousel_to_response(carousel, self._preview_base_url)

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
        items = [carousel_to_response(c, self._preview_base_url) for c in carousels]
        return CarouselListResponse(items=items, total=total)

    async def update(
        self,
        carousel_id: UUID,
        payload: CarouselUpdate,
    ) -> CarouselResponse | None:
        carousel = await self._repo.get_by_id_for_update(carousel_id)
        if carousel is None:
            return None
        format_dict = _format_to_dict(payload.format) if payload.format is not None else None
        source_payload = None
        if payload.video_url is not None:
            if carousel.source_type != SourceTypeEnum.video:
                raise ValueError("video_url can only be set for video carousels")
            merged = dict(carousel.source_payload or {})
            merged["video_url"] = payload.video_url
            merged.pop("video_key", None)
            source_payload = merged
        updated = await self._repo.update(
            carousel,
            title=payload.title,
            format=format_dict,
            source_payload=source_payload,
        )
        return carousel_to_response(updated, self._preview_base_url)

    async def set_video_key(self, carousel_id: UUID, video_key: str) -> CarouselResponse | None:
        """Set source_payload.video_key for video source and clear video_url."""
        carousel = await self._repo.get_by_id_for_update(carousel_id)
        if carousel is None:
            return None
        if carousel.source_type != SourceTypeEnum.video:
            raise ValueError("video_key can only be set for video carousels")
        merged = dict(carousel.source_payload or {})
        merged["video_key"] = video_key
        merged.pop("video_url", None)
        updated = await self._repo.update(carousel, source_payload=merged)
        return carousel_to_response(updated, self._preview_base_url)
