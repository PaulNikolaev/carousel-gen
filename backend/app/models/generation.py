"""Generation ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import GenerationStatusEnum

if TYPE_CHECKING:
    from app.models.carousel import Carousel


class Generation(Base):
    __tablename__ = "generations"

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
    status: Mapped[GenerationStatusEnum] = mapped_column(
        Enum(GenerationStatusEnum, name="generation_status_enum", create_type=True),
        nullable=False,
        default=GenerationStatusEnum.queued,
        server_default=text("'queued'::generation_status_enum"),
    )
    tokens_estimate: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
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

    carousel: Mapped[Carousel] = relationship("Carousel", back_populates="generations")
