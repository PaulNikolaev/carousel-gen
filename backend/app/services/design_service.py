"""Design settings: get-or-create CarouselDesign, partial update, optional reset slide overrides."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.carousel import Carousel
from app.models.carousel_design import CarouselDesign
from app.models.enums import BackgroundTypeEnum, TemplateEnum
from app.models.slide import Slide
from app.repositories.carousel_repository import CarouselRepository
from app.schemas.carousel import CarouselWithDesignResponse
from app.schemas.design import DesignOut, DesignResponse, DesignUpdate
from app.services.response_utils import carousel_to_response

# Keys stored in slide.design_overrides (flat, same as DesignOut field names).
_DESIGN_OVERRIDE_KEYS = (
    "template",
    "background_type",
    "background_value",
    "overlay",
    "padding",
    "alignment_h",
    "alignment_v",
    "header_enabled",
    "header_text",
    "footer_enabled",
    "footer_text",
)


def _design_out_from_carousel_and_overrides(
    design: CarouselDesign, overrides: dict
) -> DesignOut:
    """Build DesignOut from CarouselDesign and optional flat overrides (only non-null keys applied)."""
    data = {
        "template": design.template,
        "background_type": design.background_type,
        "background_value": design.background_value or "#FFFFFF",
        "overlay": design.overlay,
        "padding": design.padding,
        "alignment_h": design.alignment_h or "center",
        "alignment_v": design.alignment_v or "center",
        "header_enabled": design.header_enabled,
        "header_text": design.header_text or "",
        "footer_enabled": design.footer_enabled,
        "footer_text": design.footer_text or "",
    }
    for key in _DESIGN_OVERRIDE_KEYS:
        if key in overrides and overrides[key] is not None:
            val = overrides[key]
            if key == "template" and isinstance(val, str):
                val = TemplateEnum(val)
            elif key == "background_type" and isinstance(val, str):
                val = BackgroundTypeEnum(val)
            data[key] = val
    return DesignOut(**data)


def _design_update_to_flat_overrides(payload: DesignUpdate) -> dict:
    """Convert DesignUpdate to flat dict for design_overrides (only set keys)."""
    out: dict = {}
    if payload.template is not None:
        out["template"] = payload.template
    if payload.background is not None:
        if payload.background.type is not None:
            out["background_type"] = payload.background.type
        if payload.background.value is not None:
            out["background_value"] = payload.background.value
        if payload.background.overlay is not None:
            out["overlay"] = payload.background.overlay
    if payload.layout is not None:
        if payload.layout.padding is not None:
            out["padding"] = payload.layout.padding
        if payload.layout.alignment_h is not None:
            out["alignment_h"] = payload.layout.alignment_h
        if payload.layout.alignment_v is not None:
            out["alignment_v"] = payload.layout.alignment_v
    if payload.header is not None:
        if payload.header.enabled is not None:
            out["header_enabled"] = payload.header.enabled
        if payload.header.text is not None:
            out["header_text"] = payload.header.text
    if payload.footer is not None:
        if payload.footer.enabled is not None:
            out["footer_enabled"] = payload.footer.enabled
        if payload.footer.text is not None:
            out["footer_text"] = payload.footer.text
    return out


class DesignService:
    """Update carousel design (create design if missing); optionally reset slide design_overrides."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._carousel_repo = CarouselRepository(session)
        self._preview_base_url = get_settings().PREVIEW_BASE_URL

    async def get_design(
        self, carousel_id: UUID, slide_id: UUID | None = None
    ) -> DesignResponse | None:
        """Return design for carousel (get-or-create). If slide_id given, return effective design for that slide (carousel + overrides). Returns None if carousel or slide not found."""
        carousel = await self._carousel_repo.get_by_id(carousel_id)
        if carousel is None:
            return None
        design = await self._get_or_create_design(carousel_id)
        await self._session.refresh(design)
        if slide_id is not None:
            slide = await self._get_slide(carousel_id, slide_id)
            if slide is None:
                return None
            design_out = _design_out_from_carousel_and_overrides(
                design, slide.design_overrides or {}
            )
            return DesignResponse(design=design_out)
        return DesignResponse(design=DesignOut.model_validate(design))

    async def update_design(
        self,
        carousel_id: UUID,
        payload: DesignUpdate,
        *,
        apply_to_all: bool = False,
        slide_id: UUID | None = None,
    ) -> CarouselWithDesignResponse | None:
        carousel = await self._carousel_repo.get_by_id_for_update(carousel_id)
        if carousel is None:
            return None

        if slide_id is not None and not apply_to_all:
            return await self._update_slide_design_overrides(
                carousel_id, slide_id, payload, carousel
            )

        design = await self._get_or_create_design(carousel_id)
        self._apply_design_update(design, payload)
        await self._session.flush()

        if apply_to_all:
            await self._session.execute(
                sa_update(Slide)
                .where(Slide.carousel_id == carousel_id)
                .values(design_overrides={})
            )

        await self._session.refresh(carousel)
        await self._session.refresh(design)
        base = carousel_to_response(carousel, self._preview_base_url)
        design_out = DesignOut.model_validate(design)
        return CarouselWithDesignResponse(**base.model_dump(), design=design_out)

    async def _get_slide(self, carousel_id: UUID, slide_id: UUID) -> Slide | None:
        result = await self._session.execute(
            select(Slide).where(
                Slide.id == slide_id, Slide.carousel_id == carousel_id
            )
        )
        return result.scalar_one_or_none()

    async def _get_slide_for_update(
        self, carousel_id: UUID, slide_id: UUID
    ) -> Slide | None:
        result = await self._session.execute(
            select(Slide)
            .where(Slide.id == slide_id, Slide.carousel_id == carousel_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def _update_slide_design_overrides(
        self,
        carousel_id: UUID,
        slide_id: UUID,
        payload: DesignUpdate,
        carousel: Carousel,
    ) -> CarouselWithDesignResponse | None:
        slide = await self._get_slide_for_update(carousel_id, slide_id)
        if slide is None:
            return None
        design = await self._get_or_create_design(carousel_id)
        flat = _design_update_to_flat_overrides(payload)
        current = dict(slide.design_overrides or {})
        for key, value in flat.items():
            current[key] = value
        slide.design_overrides = current
        await self._session.flush()
        await self._session.refresh(slide)
        await self._session.refresh(design)
        base = carousel_to_response(carousel, self._preview_base_url)
        design_out = _design_out_from_carousel_and_overrides(design, current)
        return CarouselWithDesignResponse(**base.model_dump(), design=design_out)

    async def _get_or_create_design(self, carousel_id: UUID) -> CarouselDesign:
        result = await self._session.execute(
            select(CarouselDesign).where(CarouselDesign.carousel_id == carousel_id)
        )
        design = result.scalar_one_or_none()
        if design is not None:
            return design
        design = CarouselDesign(
            carousel_id=carousel_id,
            template=TemplateEnum.classic,
            background_type=BackgroundTypeEnum.color,
            background_value="#FFFFFF",
            overlay=0.0,
            padding=24,
            alignment_h="center",
            alignment_v="center",
            header_enabled=True,
            header_text="",
            footer_enabled=True,
            footer_text="",
        )
        self._session.add(design)
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            result = await self._session.execute(
                select(CarouselDesign).where(CarouselDesign.carousel_id == carousel_id)
            )
            design = result.scalar_one()
        await self._session.refresh(design)
        return design

    def _apply_design_update(self, design: CarouselDesign, payload: DesignUpdate) -> None:
        if payload.template is not None:
            design.template = payload.template
        if payload.background is not None:
            if payload.background.type is not None:
                design.background_type = payload.background.type
            if payload.background.value is not None:
                design.background_value = payload.background.value
            if payload.background.overlay is not None:
                design.overlay = payload.background.overlay
        if payload.layout is not None:
            if payload.layout.padding is not None:
                design.padding = payload.layout.padding
            if payload.layout.alignment_h is not None:
                design.alignment_h = payload.layout.alignment_h
            if payload.layout.alignment_v is not None:
                design.alignment_v = payload.layout.alignment_v
        if payload.header is not None:
            if payload.header.enabled is not None:
                design.header_enabled = payload.header.enabled
            if payload.header.text is not None:
                design.header_text = payload.header.text
        if payload.footer is not None:
            if payload.footer.enabled is not None:
                design.footer_enabled = payload.footer.enabled
            if payload.footer.text is not None:
                design.footer_text = payload.footer.text
