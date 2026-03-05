"""Design settings: get-or-create CarouselDesign, partial update, optional reset slide overrides."""

from uuid import UUID

from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.carousel_design import CarouselDesign
from app.models.enums import BackgroundTypeEnum, TemplateEnum
from app.models.slide import Slide
from app.repositories.carousel_repository import CarouselRepository
from app.schemas.carousel import CarouselWithDesignResponse
from app.schemas.design import DesignOut, DesignUpdate
from app.services.response_utils import carousel_to_response


class DesignService:
    """Update carousel design (create design if missing); optionally reset slide design_overrides."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._carousel_repo = CarouselRepository(session)
        self._preview_base_url = get_settings().PREVIEW_BASE_URL

    async def update_design(
        self,
        carousel_id: UUID,
        payload: DesignUpdate,
        *,
        apply_to_all: bool = False,
    ) -> CarouselWithDesignResponse | None:
        carousel = await self._carousel_repo.get_by_id_for_update(carousel_id)
        if carousel is None:
            return None

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
            background_value="",
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
        await self._session.flush()
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
