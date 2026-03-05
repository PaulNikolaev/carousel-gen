"""Carousel CRUD API: create draft, list, get by id, update, video upload."""

import io
from uuid import UUID

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.slides import router as slides_router
from app.core.database import get_db
from app.models.enums import CarouselStatusEnum, SourceTypeEnum
from app.schemas.carousel import (
    CarouselCreate,
    CarouselListResponse,
    CarouselResponse,
    CarouselUpdate,
)
from app.services.carousel_service import CarouselService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/carousels", tags=["carousels"])
router.include_router(slides_router, prefix="/{carousel_id:uuid}/slides")

VIDEO_MAX_SIZE = 50 * 1024 * 1024
VIDEO_EXTENSIONS: set[str] = {".mp4", ".mov", ".avi"}
VIDEO_MIME_TYPES: set[str] = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
}


def _get_service(session: AsyncSession = Depends(get_db)) -> CarouselService:
    return CarouselService(session)


def _get_storage() -> StorageService:
    return StorageService()


def _validate_video_file(filename: str, content_type: str | None) -> None:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only mp4, mov, avi video formats are allowed",
        )
    if content_type not in VIDEO_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Video content type not allowed")


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
    try:
        carousel = await service.update(carousel_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if carousel is None:
        raise HTTPException(status_code=404, detail="Carousel not found")
    return carousel


@router.post("/{carousel_id:uuid}/video", response_model=CarouselResponse)
async def upload_carousel_video(
    carousel_id: UUID,
    file: UploadFile,
    service: CarouselService = Depends(_get_service),
    storage: StorageService = Depends(_get_storage),
) -> CarouselResponse:
    """Upload video file for a carousel with source_type=video. Sets source_payload.video_key."""
    carousel = await service.get_by_id(carousel_id)
    if carousel is None:
        raise HTTPException(status_code=404, detail="Carousel not found")
    if carousel.source_type != SourceTypeEnum.video:
        raise HTTPException(
            status_code=400,
            detail="Carousel source type must be video",
        )
    if not file.filename or not file.filename.strip():
        raise HTTPException(status_code=400, detail="Missing filename")
    filename = file.filename.strip()
    _validate_video_file(filename, file.content_type)

    content = await file.read(VIDEO_MAX_SIZE + 1)
    if len(content) > VIDEO_MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Video too large (max {VIDEO_MAX_SIZE // (1024*1024)} MB)",
        )

    try:
        _, key = await storage.upload_file(
            io.BytesIO(content),
            filename,
            prefix="carousels/video",
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(
            status_code=502,
            detail=f"Upload failed: {e!s}",
        ) from e

    try:
        updated = await service.set_video_key(carousel_id, key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if updated is None:
        raise HTTPException(status_code=404, detail="Carousel not found")
    return updated
