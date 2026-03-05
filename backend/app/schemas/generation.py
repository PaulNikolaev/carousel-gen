"""Pydantic schemas for Generation API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import GenerationStatusEnum


class StartGenerationRequest(BaseModel):
    """POST /generations body."""

    carousel_id: UUID


class StartGenerationResponse(BaseModel):
    """POST /generations response."""

    generation_id: UUID
    tokens_estimate: int


class GenerationSlideItem(BaseModel):
    """Single slide in generation result (when status=done)."""

    order: int
    title: str
    body: str
    footer: str


class GenerationListItem(BaseModel):
    """Single item in GET /carousels/{id}/generations list."""

    id: UUID
    created_at: datetime
    status: GenerationStatusEnum
    tokens_used: int | None

    model_config = {"from_attributes": True}


class CarouselGenerationsResponse(BaseModel):
    """GET /carousels/{id}/generations response."""

    items: list[GenerationListItem]


class GenerationResponse(BaseModel):
    """GET /generations/{id} response."""

    id: UUID
    carousel_id: UUID
    status: GenerationStatusEnum
    tokens_estimate: int
    tokens_used: int | None
    result: list[GenerationSlideItem] | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
