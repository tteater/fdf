from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import PriceHistory
from app.database.repositories.base import BaseRepository


class PriceHistoryRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(
        self,
        *,
        tracked_product_id: int,
        price: Decimal | None,
        original_price: Decimal | None,
        discount_percent: Decimal | None,
        is_available: bool,
        scrape_strategy: str,
        checked_at: datetime,
    ) -> PriceHistory:
        item = PriceHistory(
            tracked_product_id=tracked_product_id,
            price=price,
            original_price=original_price,
            discount_percent=discount_percent,
            is_available=is_available,
            scrape_strategy=scrape_strategy,
            checked_at=checked_at,
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_recent(self, tracked_product_id: int, limit: int = 20) -> list[PriceHistory]:
        result = await self.session.execute(
            select(PriceHistory)
            .where(PriceHistory.tracked_product_id == tracked_product_id)
            .order_by(PriceHistory.checked_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
