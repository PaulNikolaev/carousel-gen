"""Async CRUD for Carousel model."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carousel import Carousel
from app.models.enums import CarouselStatusEnum, SourceTypeEnum


class CarouselRepository:
    """Repository for Carousel with async create, get_by_id, list, update."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        title: str = "",
        source_type: SourceTypeEnum,
        source_payload: dict,
        format: dict,
        language: str = "ru",
        slides_count: int = 0,
    ) -> Carousel:
        carousel = Carousel(
            title=title,
            source_type=source_type,
            source_payload=source_payload,
            format=format,
            status=CarouselStatusEnum.draft,
            language=language,
            slides_count=slides_count,
        )
        self._session.add(carousel)
        await self._session.flush()
        await self._session.refresh(carousel)
        return carousel

    async def get_by_id(self, carousel_id: UUID) -> Carousel | None:
        result = await self._session.execute(
            select(Carousel).where(Carousel.id == carousel_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, carousel_id: UUID) -> Carousel | None:
        result = await self._session.execute(
            select(Carousel).where(Carousel.id == carousel_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        status: CarouselStatusEnum | None = None,
        lang: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Carousel], int]:
        q = select(Carousel)
        count_q = select(func.count()).select_from(Carousel)
        if status is not None:
            q = q.where(Carousel.status == status)
            count_q = count_q.where(Carousel.status == status)
        if lang is not None:
            q = q.where(Carousel.language == lang)
            count_q = count_q.where(Carousel.language == lang)
        total_result = await self._session.execute(count_q)
        total = total_result.scalar() or 0
        q = q.order_by(Carousel.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all()), total

    async def update(
        self,
        carousel: Carousel,
        *,
        title: str | None = None,
        format: dict | None = None,
        status: CarouselStatusEnum | None = None,
        source_payload: dict | None = None,
        slides_count: int | None = None,
    ) -> Carousel:
        if title is not None:
            carousel.title = title
        if format is not None:
            carousel.format = format
        if status is not None:
            carousel.status = status
        if source_payload is not None:
            carousel.source_payload = source_payload
        if slides_count is not None:
            carousel.slides_count = slides_count
        await self._session.flush()
        await self._session.refresh(carousel)
        return carousel

    async def delete_by_id(self, carousel_id: UUID) -> bool:
        """Delete carousel by id. Returns True if deleted, False if not found."""
        carousel = await self.get_by_id(carousel_id)
        if carousel is None:
            return False
        await self._session.delete(carousel)
        await self._session.flush()
        return True
