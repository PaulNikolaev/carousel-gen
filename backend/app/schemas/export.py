"""Pydantic schemas for Export API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import ExportStatusEnum


class StartExportRequest(BaseModel):
    """POST /exports body."""

    carousel_id: UUID


class StartExportResponse(BaseModel):
    """POST /exports response."""

    export_id: UUID


class ExportResponse(BaseModel):
    """GET /exports/{id} response."""

    id: UUID
    carousel_id: UUID
    status: ExportStatusEnum
    download_url: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
