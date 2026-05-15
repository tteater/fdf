from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import FailedJob
from app.database.repositories.base import BaseRepository


class FailedJobRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(
        self,
        *,
        job_name: str,
        status: str,
        entity_id: str | None,
        attempt: int,
        error_message: str,
        traceback: str | None,
        next_retry_at: datetime | None,
    ) -> FailedJob:
        item = FailedJob(
            job_name=job_name,
            status=status,
            entity_id=entity_id,
            attempt=attempt,
            error_message=error_message,
            traceback=traceback,
            next_retry_at=next_retry_at,
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(FailedJob))
        return int(result.scalar_one())
