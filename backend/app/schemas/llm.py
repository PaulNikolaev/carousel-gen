"""Pydantic schemas for LLM slide generation result."""

from pydantic import BaseModel, Field, RootModel

TITLE_MAX = 60
BODY_MAX = 300

__all__ = ["SlideGenerationItem", "SlideGenerationResult", "TITLE_MAX", "BODY_MAX"]


class SlideGenerationItem(BaseModel):
    """Single slide item from LLM: order, title, body, footer."""

    order: int = Field(..., ge=1)
    title: str = Field(..., max_length=TITLE_MAX)
    body: str = Field(..., max_length=BODY_MAX)
    footer: str = ""


class SlideGenerationResult(RootModel[list[SlideGenerationItem]]):
    """Array of slide items from LLM, validated."""
