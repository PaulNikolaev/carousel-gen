"""Generations API: POST start generation, GET generation by id, GET stream SSE."""

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import CarouselConflictError, CarouselNotFoundError
from app.models.enums import GenerationStatusEnum
from app.models.generation import Generation
from app.schemas.generation import (
    GenerationResponse,
    GenerationSlideItem,
    StartGenerationRequest,
    StartGenerationResponse,
)
from app.services.generation_service import GenerationService

router = APIRouter(prefix="/generations", tags=["generations"])

SSE_POLL_INTERVAL = 1.5


def _get_service(session: AsyncSession = Depends(get_db)) -> GenerationService:
    return GenerationService(session)


def _generation_to_response(gen: Generation) -> GenerationResponse:
    result_list = None
    if gen.result:
        raw = (
            gen.result
            if isinstance(gen.result, list)
            else (gen.result.get("slides") or [] if isinstance(gen.result, dict) else [])
        )
        result_list = [GenerationSlideItem.model_validate(x) for x in raw]
    return GenerationResponse(
        id=gen.id,
        carousel_id=gen.carousel_id,
        status=gen.status,
        tokens_estimate=gen.tokens_estimate,
        tokens_used=gen.tokens_used,
        result=result_list,
        error_message=gen.error_message,
        created_at=gen.created_at,
        updated_at=gen.updated_at,
    )


@router.post("", response_model=StartGenerationResponse, status_code=202)
async def start_generation(
    payload: StartGenerationRequest,
    background_tasks: BackgroundTasks,
    service: GenerationService = Depends(_get_service),
) -> StartGenerationResponse:
    try:
        return await service.start_generation(
            payload.carousel_id,
            background_tasks=background_tasks,
        )
    except CarouselNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Carousel not found",
        )
    except CarouselConflictError:
        raise HTTPException(
            status_code=409,
            detail="Carousel is not in draft/ready/failed or has an active generation",
        )


@router.get("/{generation_id:uuid}", response_model=GenerationResponse)
async def get_generation(
    generation_id: UUID,
    service: GenerationService = Depends(_get_service),
) -> GenerationResponse:
    gen = await service.get_by_id(generation_id)
    if gen is None:
        raise HTTPException(status_code=404, detail="Generation not found")
    return _generation_to_response(gen)


async def _generation_stream_events(
    generation_id: UUID,
    service: GenerationService,
):
    """Async generator: yield SSE data lines until status is done or failed."""
    while True:
        gen = await service.get_by_id(generation_id)
        if gen is None:
            return
        resp = _generation_to_response(gen)
        payload = resp.model_dump(mode="json")
        yield f"data: {json.dumps(payload)}\n\n"
        if gen.status in (GenerationStatusEnum.done, GenerationStatusEnum.failed):
            return
        await asyncio.sleep(SSE_POLL_INTERVAL)


@router.get("/{generation_id:uuid}/stream")
async def stream_generation(
    generation_id: UUID,
    service: GenerationService = Depends(_get_service),
) -> StreamingResponse:
    """SSE stream of generation status until done or failed."""
    gen = await service.get_by_id(generation_id)
    if gen is None:
        raise HTTPException(status_code=404, detail="Generation not found")
    return StreamingResponse(
        _generation_stream_events(generation_id, service),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
