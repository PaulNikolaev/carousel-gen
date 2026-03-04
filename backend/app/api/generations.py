"""Generations API: POST start generation, GET generation by id."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import CarouselConflictError, CarouselNotFoundError
from app.models.generation import Generation
from app.schemas.generation import (
    GenerationResponse,
    GenerationSlideItem,
    StartGenerationRequest,
    StartGenerationResponse,
)
from app.services.generation_service import GenerationService

router = APIRouter(prefix="/generations", tags=["generations"])


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
            detail="Carousel is not in draft or has an active generation",
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
