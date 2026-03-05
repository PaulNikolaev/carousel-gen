"""Pydantic schemas for CarouselDesign API."""

from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import BackgroundTypeEnum, TemplateEnum


class DesignBackgroundUpdate(BaseModel):
    """Optional background fields for PATCH."""

    type: BackgroundTypeEnum | None = None
    value: str | None = Field(None, max_length=512)
    overlay: float | None = Field(None, ge=0.0, le=1.0)


class DesignLayoutUpdate(BaseModel):
    """Optional layout fields for PATCH."""

    padding: int | None = Field(None, ge=0)
    alignment_h: Literal["left", "center", "right"] | None = None
    alignment_v: Literal["top", "center", "bottom"] | None = None


class DesignHeaderUpdate(BaseModel):
    """Optional header fields for PATCH."""

    enabled: bool | None = None
    text: str | None = Field(None, max_length=512)


class DesignFooterUpdate(BaseModel):
    """Optional footer fields for PATCH."""

    enabled: bool | None = None
    text: str | None = Field(None, max_length=512)


class DesignUpdate(BaseModel):
    """Payload for PATCH design: all fields optional."""

    template: TemplateEnum | None = None
    background: DesignBackgroundUpdate | None = None
    layout: DesignLayoutUpdate | None = None
    header: DesignHeaderUpdate | None = None
    footer: DesignFooterUpdate | None = None


class DesignOut(BaseModel):
    """Design snapshot for API response (template, background, layout, header, footer)."""

    template: TemplateEnum
    background_type: BackgroundTypeEnum
    background_value: str
    overlay: float
    padding: int
    alignment_h: str
    alignment_v: str
    header_enabled: bool
    header_text: str
    footer_enabled: bool
    footer_text: str

    model_config = {"from_attributes": True}
