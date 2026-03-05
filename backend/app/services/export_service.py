"""Export business logic: start with BackgroundTask, render to ZIP, upload to S3."""

import logging
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.exceptions import CarouselNotFoundError
from app.models.enums import ExportStatusEnum
from app.models.export import Export
from app.repositories.carousel_repository import CarouselRepository
from app.repositories.export_repository import ExportRepository
from app.schemas.export import StartExportResponse
from app.services.render_service import render_carousel_to_zip
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


async def _run_export_task(export_id: UUID) -> None:
    async with async_session_factory() as session:
        export_repo = ExportRepository(session)
        export = await export_repo.get_by_id(export_id)
        if not export:
            return
        await export_repo.update(export, status=ExportStatusEnum.running)
        await session.commit()

        storage = StorageService()
        try:
            s3_key = await render_carousel_to_zip(
                export.carousel_id,
                session,
                storage=storage,
                export_id=export_id,
            )
            await export_repo.update(
                export,
                status=ExportStatusEnum.done,
                s3_key=s3_key,
            )
            await session.commit()
        except Exception as e:
            logger.exception("Export %s failed", export_id)
            await session.rollback()
            export = await export_repo.get_by_id(export_id)
            if export:
                await export_repo.update(
                    export,
                    status=ExportStatusEnum.failed,
                    error_message=str(e),
                )
                await session.commit()


class ExportService:
    """Service for starting export and querying export status."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._carousel_repo = CarouselRepository(session)
        self._export_repo = ExportRepository(session)

    async def start_export(
        self,
        carousel_id: UUID,
        background_tasks: BackgroundTasks,
    ) -> StartExportResponse:
        """Start export or return existing active export_id (idempotent)."""
        carousel = await self._carousel_repo.get_by_id(carousel_id)
        if carousel is None:
            raise CarouselNotFoundError()
        existing = await self._export_repo.get_active_for_carousel(carousel_id)
        if existing is not None:
            return StartExportResponse(export_id=existing.id)
        export = await self._export_repo.create(carousel_id=carousel_id)
        background_tasks.add_task(_run_export_task, export.id)
        return StartExportResponse(export_id=export.id)

    async def get_by_id(self, export_id: UUID) -> Export | None:
        return await self._export_repo.get_by_id(export_id)
