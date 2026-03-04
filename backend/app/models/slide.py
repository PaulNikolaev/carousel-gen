"""Slide ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.carousel import Carousel


class Slide(Base):
    __tablename__ = "slides"
    __table_args__ = (
        UniqueConstraint("carousel_id", "order", name="uq_slides_carousel_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    carousel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carousels.id", ondelete="CASCADE"),
        nullable=False,
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    footer: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    design_overrides: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    carousel: Mapped[Carousel] = relationship("Carousel", back_populates="slides")
