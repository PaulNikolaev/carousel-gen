"""Slides API: list slides of a carousel, update one slide."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.slide import SlideResponse, SlideUpdate
from app.services.slide_service import SlideService

router = APIRouter(tags=["slides"])


def _get_service(session: AsyncSession = Depends(get_db)) -> SlideService:
    return SlideService(session)


@router.get("", response_model=list[SlideResponse])
async def list_slides(
    carousel_id: UUID,
    service: SlideService = Depends(_get_service),
) -> list[SlideResponse]:
    slides = await service.list_slides(carousel_id)
    if slides is None:
        raise HTTPException(status_code=404, detail="Carousel not found")
    return slides


@router.patch("/{slide_id:uuid}", response_model=SlideResponse)
async def update_slide(
    carousel_id: UUID,
    slide_id: UUID,
    payload: SlideUpdate,
    service: SlideService = Depends(_get_service),
) -> SlideResponse:
    slide = await service.update_slide(carousel_id, slide_id, payload)
    if slide is None:
        raise HTTPException(status_code=404, detail="Carousel or slide not found")
    return slide
