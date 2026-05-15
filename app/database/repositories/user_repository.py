from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        *,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        language_code: str | None,
        timezone: str,
    ) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.username = username
            user.first_name = first_name
            user.language_code = language_code
            user.timezone = timezone
            return user

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            language_code=language_code,
            timezone=timezone,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def count_users(self) -> int:
        from sqlalchemy import func

        result = await self.session.execute(select(func.count()).select_from(User))
        return int(result.scalar_one())
