"""Pydantic schemas for Carousel API."""

from datetime import datetime
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import CarouselStatusEnum, SourceTypeEnum

from app.schemas.design import DesignOut


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
    slides_count: int = Field(0, ge=0)


class CarouselUpdate(BaseModel):
    """Payload for PATCH: update title, format and/or video_url."""

    title: str | None = None
    format: FormatSchema | None = None
    video_url: str | None = None

    @field_validator("video_url")
    @classmethod
    def validate_video_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        parsed = urlparse(v)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("video_url must be a valid http/https URL")
        return v


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


class CarouselWithDesignResponse(CarouselResponse):
    """Carousel response with design snapshot (for PATCH .../design)."""

    design: DesignOut


class CarouselListResponse(BaseModel):
    """Paginated list of carousels."""

    items: list[CarouselResponse]
    total: int
