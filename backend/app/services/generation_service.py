"""Generation business logic: start with BackgroundTask, run LLM, persist slides."""

import time
from uuid import UUID

import structlog
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

logger = structlog.get_logger()


async def _run_generation_task(generation_id: UUID) -> None:
    started_at = time.perf_counter()

    async with async_session_factory() as session:
        gen_repo = GenerationRepository(session)
        slide_repo = SlideRepository(session)
        carousel_repo = CarouselRepository(session)
        try:
            gen = await gen_repo.get_by_id(generation_id, load_carousel=True)
            if not gen or not gen.carousel:
                return
            carousel = gen.carousel
            log = logger.bind(
                generation_id=str(generation_id), carousel_id=str(carousel.id)
            )
            log.info("generation_started")
            await gen_repo.update(gen, status=GenerationStatusEnum.running)

            style_hint = None
            slides_count = carousel.slides_count
            if isinstance(carousel.format, dict):
                style_hint = carousel.format.get("style_hint")
                if slides_count <= 0:
                    slides_count = carousel.format.get("slides_count") or 8
            if slides_count <= 0:
                slides_count = 8
            slides_result, tokens_used = await generate_slides(
                carousel.source_payload,
                carousel.language,
                slides_count,
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
            duration_ms = (time.perf_counter() - started_at) * 1000
            log.info(
                "generation_finished",
                tokens_used=tokens_used,
                duration_ms=round(duration_ms, 2),
            )
        except Exception as e:
            await session.rollback()
            duration_ms = (time.perf_counter() - started_at) * 1000
            carousel_id = None
            try:
                async with async_session_factory() as session2:
                    gen_repo2 = GenerationRepository(session2)
                    carousel_repo2 = CarouselRepository(session2)
                    gen = await gen_repo2.get_by_id(generation_id, load_carousel=True)
                    if gen:
                        carousel_id = str(gen.carousel_id) if gen.carousel_id else None
                        await gen_repo2.update(
                            gen,
                            status=GenerationStatusEnum.failed,
                            error_message=str(e),
                        )
                        if gen.carousel:
                            await carousel_repo2.update(
                                gen.carousel, status=CarouselStatusEnum.failed
                            )
                    await session2.commit()
            except Exception as inner_exc:
                logger.warning(
                    "generation_status_update_failed",
                    generation_id=str(generation_id),
                    inner_error=repr(inner_exc),
                )
            log = logger.bind(
                generation_id=str(generation_id),
                carousel_id=carousel_id,
            )
            log.error(
                "generation_failed",
                error=repr(e),
                duration_ms=round(duration_ms, 2),
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
        allowed_statuses = (
            CarouselStatusEnum.draft,
            CarouselStatusEnum.ready,
            CarouselStatusEnum.failed,
        )
        if active is not None or carousel.status not in allowed_statuses:
            raise CarouselConflictError()
        tokens_estimate = -1  # reserved: pre-run token count not implemented
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

    async def list_for_carousel(
        self, carousel_id: UUID, *, limit: int = 50
    ) -> list[Generation]:
        """Return generations for carousel, ordered by created_at DESC."""
        return await self._gen_repo.list_by_carousel_id(carousel_id, limit=limit)
