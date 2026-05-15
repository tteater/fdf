from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Notification
from app.database.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(
        self,
        *,
        user_id: int,
        tracked_product_id: int,
        notification_type: str,
        old_price: Decimal | None,
        new_price: Decimal | None,
        telegram_message_id: int | None,
    ) -> Notification:
        item = Notification(
            user_id=user_id,
            tracked_product_id=tracked_product_id,
            notification_type=notification_type,
            old_price=old_price,
            new_price=new_price,
            telegram_message_id=telegram_message_id,
            delivered_at=datetime.utcnow(),
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def count_total(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(Notification))
        return int(result.scalar_one())
