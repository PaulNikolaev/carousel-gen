"""Carousel CRUD API: create draft, list, get by id, update."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.enums import CarouselStatusEnum
from app.schemas.carousel import (
    CarouselCreate,
    CarouselListResponse,
    CarouselResponse,
    CarouselUpdate,
)
from app.services.carousel_service import CarouselService

router = APIRouter(prefix="/carousels", tags=["carousels"])


def _get_service(session: AsyncSession = Depends(get_db)) -> CarouselService:
    return CarouselService(session)


@router.post("", response_model=CarouselResponse, status_code=201)
async def create_carousel(
    payload: CarouselCreate,
    service: CarouselService = Depends(_get_service),
) -> CarouselResponse:
    return await service.create_draft(payload)


@router.get("", response_model=CarouselListResponse)
async def list_carousels(
    status: CarouselStatusEnum | None = None,
    lang: str | None = None,
    skip: int = 0,
    limit: int = 20,
    service: CarouselService = Depends(_get_service),
) -> CarouselListResponse:
    return await service.list(status=status, lang=lang, skip=skip, limit=limit)


@router.get("/{carousel_id:uuid}", response_model=CarouselResponse)
async def get_carousel(
    carousel_id: UUID,
    service: CarouselService = Depends(_get_service),
) -> CarouselResponse:
    carousel = await service.get_by_id(carousel_id)
    if carousel is None:
        raise HTTPException(status_code=404, detail="Carousel not found")
    return carousel


@router.patch("/{carousel_id:uuid}", response_model=CarouselResponse)
async def update_carousel(
    carousel_id: UUID,
    payload: CarouselUpdate,
    service: CarouselService = Depends(_get_service),
) -> CarouselResponse:
    carousel = await service.update(carousel_id, payload)
    if carousel is None:
        raise HTTPException(status_code=404, detail="Carousel not found")
    return carousel
