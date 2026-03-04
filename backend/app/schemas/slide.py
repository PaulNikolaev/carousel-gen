"""Pydantic schemas for Slide API."""

from uuid import UUID

from pydantic import BaseModel


class SlideResponse(BaseModel):
    """Slide in API response."""

    id: UUID
    carousel_id: UUID
    order: int
    title: str
    body: str
    footer: str
    design_overrides: dict

    model_config = {"from_attributes": True}


class SlideUpdate(BaseModel):
    """Payload for PATCH: update title, body, footer."""

    title: str | None = None
    body: str | None = None
    footer: str | None = None
