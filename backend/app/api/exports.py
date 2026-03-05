"""Exports API: POST start export, GET export by id, GET stream SSE."""

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import CarouselNotFoundError
from app.models.enums import ExportStatusEnum
from app.models.export import Export
from app.schemas.export import (
    ExportResponse,
    StartExportRequest,
    StartExportResponse,
)
from app.services.export_service import ExportService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/exports", tags=["exports"])

PRESIGNED_EXPIRES_IN = 86400
SSE_POLL_INTERVAL = 1.5


def _get_service(session: AsyncSession = Depends(get_db)) -> ExportService:
    return ExportService(session)


def _get_storage() -> StorageService:
    return StorageService()


def _export_to_response(export: Export, download_url: str | None = None) -> ExportResponse:
    return ExportResponse(
        id=export.id,
        carousel_id=export.carousel_id,
        status=export.status,
        download_url=download_url,
        error_message=export.error_message,
        created_at=export.created_at,
        updated_at=export.updated_at,
    )


@router.post("", response_model=StartExportResponse, status_code=202)
async def start_export(
    payload: StartExportRequest,
    background_tasks: BackgroundTasks,
    service: ExportService = Depends(_get_service),
) -> StartExportResponse:
    try:
        return await service.start_export(
            payload.carousel_id,
            background_tasks=background_tasks,
        )
    except CarouselNotFoundError:
        raise HTTPException(status_code=404, detail="Carousel not found")


@router.get("/{export_id:uuid}", response_model=ExportResponse)
async def get_export(
    export_id: UUID,
    service: ExportService = Depends(_get_service),
    storage: StorageService = Depends(_get_storage),
) -> ExportResponse:
    export = await service.get_by_id(export_id)
    if export is None:
        raise HTTPException(status_code=404, detail="Export not found")
    download_url = None
    if export.status == ExportStatusEnum.done and export.s3_key:
        download_url = await storage.generate_presigned_url(
            export.s3_key,
            expires_in=PRESIGNED_EXPIRES_IN,
        )
    return _export_to_response(export, download_url=download_url)


async def _export_stream_events(
    export_id: UUID,
    service: ExportService,
    storage: StorageService,
):
    """Async generator: yield SSE data lines until status is done or failed."""
    while True:
        export = await service.get_by_id(export_id)
        if export is None:
            return
        download_url = None
        if export.status == ExportStatusEnum.done and export.s3_key:
            download_url = await storage.generate_presigned_url(
                export.s3_key,
                expires_in=PRESIGNED_EXPIRES_IN,
            )
        resp = _export_to_response(export, download_url=download_url)
        payload = resp.model_dump(mode="json")
        yield f"data: {json.dumps(payload)}\n\n"
        if export.status in (ExportStatusEnum.done, ExportStatusEnum.failed):
            return
        await asyncio.sleep(SSE_POLL_INTERVAL)


@router.get("/{export_id:uuid}/stream")
async def stream_export(
    export_id: UUID,
    service: ExportService = Depends(_get_service),
    storage: StorageService = Depends(_get_storage),
) -> StreamingResponse:
    """SSE stream of export status until done or failed (includes download_url when done)."""
    export = await service.get_by_id(export_id)
    if export is None:
        raise HTTPException(status_code=404, detail="Export not found")
    return StreamingResponse(
        _export_stream_events(export_id, service, storage),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
