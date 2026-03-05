"""Generation business logic: start with BackgroundTask, run LLM, persist slides."""

import logging
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.exceptions import CarouselConflictError, CarouselNotFoundError
from app.models.enums import CarouselStatusEnum, GenerationStatusEnum
from app.models.generation import Generation
from app.repositories.carousel_repository import CarouselRepository
from app.repositories.generation_repository import GenerationRepository
from app.repositories.slide_repository import SlideRepository
from app.schemas.generation import StartGenerationResponse
from app.services.llm_service import generate_slides

logger = logging.getLogger(__name__)


async def _run_generation_task(generation_id: UUID) -> None:
    async with async_session_factory() as session:
        gen_repo = GenerationRepository(session)
        slide_repo = SlideRepository(session)
        carousel_repo = CarouselRepository(session)
        try:
            gen = await gen_repo.get_by_id(generation_id, load_carousel=True)
            if not gen or not gen.carousel:
                return
            carousel = gen.carousel
            await gen_repo.update(gen, status=GenerationStatusEnum.running)

            style_hint = None
            if isinstance(carousel.format, dict):
                style_hint = carousel.format.get("style_hint")
            slides_result, tokens_used = await generate_slides(
                carousel.source_payload,
                carousel.language,
                carousel.slides_count,
                style_hint=style_hint,
            )

            slide_items = [
                {
                    "order": item.order,
                    "title": item.title,
                    "body": item.body,
                    "footer": item.footer,
                }
                for item in slides_result
            ]
            await slide_repo.delete_by_carousel_id(carousel.id)
            await slide_repo.create_for_carousel(carousel.id, slide_items)
            await gen_repo.update(
                gen,
                status=GenerationStatusEnum.done,
                tokens_used=tokens_used,
                result=slide_items,
            )
            await carousel_repo.update(
                carousel,
                status=CarouselStatusEnum.ready,
                slides_count=len(slide_items),
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.exception("Generation %s failed", generation_id)
            try:
                async with async_session_factory() as session2:
                    gen_repo2 = GenerationRepository(session2)
                    carousel_repo2 = CarouselRepository(session2)
                    gen = await gen_repo2.get_by_id(generation_id, load_carousel=True)
                    if gen:
                        await gen_repo2.update(
                            gen,
                            status=GenerationStatusEnum.failed,
                            error_message=repr(e),
                        )
                        if gen.carousel:
                            await carousel_repo2.update(
                                gen.carousel, status=CarouselStatusEnum.failed
                            )
                    await session2.commit()
            except Exception:
                logger.exception(
                    "Failed to persist failed status for generation %s", generation_id
                )


class GenerationService:
    """Service for starting slide generation and querying generation status."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._carousel_repo = CarouselRepository(session)
        self._gen_repo = GenerationRepository(session)

    async def start_generation(
        self,
        carousel_id: UUID,
        background_tasks: BackgroundTasks,
    ) -> StartGenerationResponse:
        carousel = await self._carousel_repo.get_by_id_for_update(carousel_id)
        if carousel is None:
            raise CarouselNotFoundError()
        active = await self._gen_repo.get_active_for_carousel(carousel_id)
        if active is not None or carousel.status != CarouselStatusEnum.draft:
            raise CarouselConflictError()
        tokens_estimate = 0
        gen = await self._gen_repo.create(
            carousel_id=carousel_id,
            tokens_estimate=tokens_estimate,
        )
        await self._carousel_repo.update(carousel, status=CarouselStatusEnum.generating)
        background_tasks.add_task(_run_generation_task, gen.id)
        return StartGenerationResponse(
            generation_id=gen.id,
            tokens_estimate=tokens_estimate,
        )

    async def get_by_id(self, generation_id: UUID) -> Generation | None:
        """Return Generation model or None; caller builds response with result list."""
        return await self._gen_repo.get_by_id(generation_id, load_carousel=False)
