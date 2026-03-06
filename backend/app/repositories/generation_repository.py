"""Async CRUD for Generation model."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import GenerationStatusEnum
from app.models.generation import Generation


class GenerationRepository:
    """Repository for Generation: create, get_by_id, update status/result."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        carousel_id: UUID,
        tokens_estimate: int = 0,
    ) -> Generation:
        gen = Generation(
            carousel_id=carousel_id,
            status=GenerationStatusEnum.queued,
            tokens_estimate=tokens_estimate,
        )
        self._session.add(gen)
        await self._session.flush()
        await self._session.refresh(gen)
        return gen

    async def get_active_for_carousel(self, carousel_id: UUID) -> Generation | None:
        result = await self._session.execute(
            select(Generation)
            .where(Generation.carousel_id == carousel_id)
            .where(
                Generation.status.in_(
                    [GenerationStatusEnum.queued, GenerationStatusEnum.running]
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_carousel_id(
        self, carousel_id: UUID, *, limit: int = 50
    ) -> list[Generation]:
        result = await self._session.execute(
            select(Generation)
            .where(Generation.carousel_id == carousel_id)
            .order_by(Generation.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(
        self, generation_id: UUID, *, load_carousel: bool = False
    ) -> Generation | None:
        q = (
            select(Generation)
            .where(Generation.id == generation_id)
            .execution_options(populate_existing=True)
        )
        if load_carousel:
            q = q.options(selectinload(Generation.carousel))
        result = await self._session.execute(q)
        return result.scalar_one_or_none()

    async def update(
        self,
        generation: Generation,
        *,
        status: GenerationStatusEnum | None = None,
        tokens_used: int | None = None,
        result: dict | list | None = None,
        error_message: str | None = None,
    ) -> Generation:
        if status is not None:
            generation.status = status
        if tokens_used is not None:
            generation.tokens_used = tokens_used
        if result is not None:
            generation.result = result
        if error_message is not None:
            generation.error_message = error_message
        await self._session.flush()
        await self._session.refresh(generation)
        return generation
