from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AdminLog
from app.database.repositories.base import BaseRepository


class AdminLogRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(
        self,
        *,
        level: str,
        event: str,
        message: str,
        payload: dict | None,
    ) -> AdminLog:
        log = AdminLog(level=level, event=event, message=message, payload=payload)
        self.session.add(log)
        await self.session.flush()
        return log

    async def count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(AdminLog))
        return int(result.scalar_one())
