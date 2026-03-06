"""Async CRUD for Export model."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ExportStatusEnum
from app.models.export import Export


class ExportRepository:
    """Repository for Export: create, get_by_id, update."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_for_carousel(self, carousel_id: UUID) -> Export | None:
        """Return an export in pending or running state for this carousel, or None."""
        result = await self._session.execute(
            select(Export)
            .where(Export.carousel_id == carousel_id)
            .where(Export.status.in_([ExportStatusEnum.pending, ExportStatusEnum.running]))
            .order_by(Export.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, *, carousel_id: UUID) -> Export:
        export = Export(
            carousel_id=carousel_id,
            status=ExportStatusEnum.pending,
        )
        self._session.add(export)
        await self._session.flush()
        await self._session.refresh(export)
        return export

    async def get_by_id(self, export_id: UUID) -> Export | None:
        result = await self._session.execute(
            select(Export)
            .where(Export.id == export_id)
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        export: Export,
        *,
        status: ExportStatusEnum | None = None,
        s3_key: str | None = None,
        error_message: str | None = None,
    ) -> Export:
        if status is not None:
            export.status = status
        if s3_key is not None:
            export.s3_key = s3_key
        if error_message is not None:
            export.error_message = error_message
        await self._session.flush()
        await self._session.refresh(export)
        return export
