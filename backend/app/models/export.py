"""Export ORM model (carousel → ZIP in S3)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ExportStatusEnum

if TYPE_CHECKING:
    from app.models.carousel import Carousel


class Export(Base):
    __tablename__ = "exports"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    carousel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carousels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ExportStatusEnum] = mapped_column(
        Enum(ExportStatusEnum, name="export_status_enum", create_type=True),
        nullable=False,
        default=ExportStatusEnum.pending,
        server_default=text("'pending'::export_status_enum"),
    )
    s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    carousel: Mapped[Carousel] = relationship("Carousel", back_populates="exports")
