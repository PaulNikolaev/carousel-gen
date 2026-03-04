"""Slide business logic: list slides of a carousel, update slide content."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.carousel_repository import CarouselRepository
from app.repositories.slide_repository import SlideRepository
from app.schemas.slide import SlideResponse, SlideUpdate


class SlideService:
    """Service for listing and updating slides; returns 404 when carousel or slide missing."""

    def __init__(self, session: AsyncSession) -> None:
        self._carousel_repo = CarouselRepository(session)
        self._slide_repo = SlideRepository(session)

    async def list_slides(self, carousel_id: UUID) -> list[SlideResponse] | None:
        carousel = await self._carousel_repo.get_by_id(carousel_id)
        if carousel is None:
            return None
        slides = await self._slide_repo.list_by_carousel_id(carousel_id)
        return [SlideResponse.model_validate(s) for s in slides]

    async def update_slide(
        self,
        carousel_id: UUID,
        slide_id: UUID,
        payload: SlideUpdate,
    ) -> SlideResponse | None:
        carousel = await self._carousel_repo.get_by_id(carousel_id)
        if carousel is None:
            return None
        slide = await self._slide_repo.get_by_id(slide_id)
        if slide is None or slide.carousel_id != carousel_id:
            return None
        updated = await self._slide_repo.update(
            slide,
            title=payload.title,
            body=payload.body,
            footer=payload.footer,
        )
        return SlideResponse.model_validate(updated)
