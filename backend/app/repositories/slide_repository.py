"""Async data access for Slide model."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slide import Slide


class SlideRepository:
    """Repository for Slide: list by carousel (ordered by order), get by id, update."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_carousel_id(self, carousel_id: UUID) -> list[Slide]:
        result = await self._session.execute(
            select(Slide).where(Slide.carousel_id == carousel_id).order_by(Slide.order)
        )
        return list(result.scalars().all())

    async def get_by_id(self, slide_id: UUID) -> Slide | None:
        result = await self._session.execute(select(Slide).where(Slide.id == slide_id))
        return result.scalar_one_or_none()

    async def update(
        self,
        slide: Slide,
        *,
        title: str | None = None,
        body: str | None = None,
        footer: str | None = None,
    ) -> Slide:
        if title is None and body is None and footer is None:
            return slide
        if title is not None:
            slide.title = title
        if body is not None:
            slide.body = body
        if footer is not None:
            slide.footer = footer
        await self._session.flush()
        await self._session.refresh(slide)
        return slide
