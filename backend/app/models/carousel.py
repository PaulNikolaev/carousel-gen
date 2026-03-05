"""Carousel ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Integer, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import CarouselStatusEnum, SourceTypeEnum

if TYPE_CHECKING:
    from app.models.carousel_design import CarouselDesign
    from app.models.export import Export
    from app.models.generation import Generation
    from app.models.slide import Slide


class Carousel(Base):
    __tablename__ = "carousels"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    source_type: Mapped[SourceTypeEnum] = mapped_column(
        Enum(SourceTypeEnum, name="source_type_enum", create_type=True),
        nullable=False,
    )
    source_payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    format: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    status: Mapped[CarouselStatusEnum] = mapped_column(
        Enum(CarouselStatusEnum, name="carousel_status_enum", create_type=True),
        nullable=False,
        default=CarouselStatusEnum.draft,
    )
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="ru")
    slides_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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

    slides: Mapped[list[Slide]] = relationship(
        "Slide",
        back_populates="carousel",
        order_by="Slide.order",
        cascade="all, delete-orphan",
    )
    generations: Mapped[list[Generation]] = relationship(
        "Generation",
        back_populates="carousel",
        cascade="all, delete-orphan",
    )
    design: Mapped[CarouselDesign | None] = relationship(
        "CarouselDesign",
        back_populates="carousel",
        uselist=False,
        cascade="all, delete-orphan",
    )
    exports: Mapped[list[Export]] = relationship(
        "Export",
        back_populates="carousel",
        cascade="all, delete-orphan",
    )
