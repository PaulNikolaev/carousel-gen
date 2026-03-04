"""CarouselDesign ORM model (1:1 to Carousel)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import BackgroundTypeEnum, TemplateEnum

if TYPE_CHECKING:
    from app.models.carousel import Carousel


class CarouselDesign(Base):
    __tablename__ = "carousel_designs"

    carousel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carousels.id", ondelete="CASCADE"),
        primary_key=True,
    )
    template: Mapped[TemplateEnum] = mapped_column(
        Enum(TemplateEnum, name="template_enum", create_type=True),
        nullable=False,
    )
    background_type: Mapped[BackgroundTypeEnum] = mapped_column(
        Enum(BackgroundTypeEnum, name="background_type_enum", create_type=True),
        nullable=False,
    )
    background_value: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    overlay: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    padding: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    alignment_h: Mapped[str] = mapped_column(String(32), nullable=False, default="center")
    alignment_v: Mapped[str] = mapped_column(String(32), nullable=False, default="center")
    header_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    header_text: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    footer_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    footer_text: Mapped[str] = mapped_column(String(512), nullable=False, default="")

    carousel: Mapped[Carousel] = relationship(
        "Carousel",
        back_populates="design",
    )
