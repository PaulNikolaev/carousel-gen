"""Pydantic schemas for CarouselDesign API."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.constants import ALLOWED_FONT_FAMILIES
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


class DesignTypographyUpdate(BaseModel):
    """Optional typography fields for PATCH."""

    font_size: int | None = Field(None, ge=12, le=32)
    font_family: str | None = Field(None, max_length=128)
    font_weight: Literal["normal", "bold"] | None = None
    font_style: Literal["normal", "italic"] | None = None

    @field_validator("font_family")
    @classmethod
    def font_family_whitelist(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return v
        normalized = v.strip()[:128]
        if normalized in ALLOWED_FONT_FAMILIES:
            return normalized
        raise ValueError(
            f"font_family must be one of: {sorted(ALLOWED_FONT_FAMILIES)}"
        )


class DesignUpdate(BaseModel):
    """Payload for PATCH design: all fields optional."""

    template: TemplateEnum | None = None
    background: DesignBackgroundUpdate | None = None
    layout: DesignLayoutUpdate | None = None
    header: DesignHeaderUpdate | None = None
    footer: DesignFooterUpdate | None = None
    typography: DesignTypographyUpdate | None = None


class DesignOut(BaseModel):
    """Design snapshot for API response (template, background, layout, header, footer, typography)."""

    template: TemplateEnum
    background_type: BackgroundTypeEnum
    background_value: str
    overlay: float
    padding: int
    alignment_h: Literal["left", "center", "right"]
    alignment_v: Literal["top", "center", "bottom"]
    header_enabled: bool
    header_text: str
    footer_enabled: bool
    footer_text: str
    font_size: int = 16
    font_family: str = "system-ui"
    font_weight: Literal["normal", "bold"] = "normal"
    font_style: Literal["normal", "italic"] = "normal"

    model_config = {"from_attributes": True}


class DesignResponse(BaseModel):
    """Response for GET /carousels/{id}/design."""

    design: DesignOut
