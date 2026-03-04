"""Pydantic schemas for Carousel API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import CarouselStatusEnum, SourceTypeEnum


class FormatSchema(BaseModel):
    """Format JSONB: slides_count, language, style_hint."""

    slides_count: int | None = None
    language: str | None = None
    style_hint: str | None = None


class CarouselCreate(BaseModel):
    """Payload for creating a draft carousel."""

    title: str = ""
    source_type: SourceTypeEnum = SourceTypeEnum.text
    source_payload: dict = Field(default_factory=dict)
    format: FormatSchema = Field(default_factory=FormatSchema)
    language: str = "ru"
    slides_count: int = 0


class CarouselUpdate(BaseModel):
    """Payload for PATCH: update title and/or format."""

    title: str | None = None
    format: FormatSchema | None = None


class CarouselResponse(BaseModel):
    """Carousel with preview URL of first slide."""

    id: UUID
    title: str
    source_type: SourceTypeEnum
    source_payload: dict
    format: dict
    status: CarouselStatusEnum
    language: str
    slides_count: int
    created_at: datetime
    updated_at: datetime
    preview_url: str

    model_config = {"from_attributes": True}


class CarouselListResponse(BaseModel):
    """Paginated list of carousels."""

    items: list[CarouselResponse]
    total: int
