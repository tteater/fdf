from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import ProductStatus
from app.database.models import TrackedProduct
from app.database.repositories.base import BaseRepository


class TrackedProductRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def count_for_user(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(TrackedProduct).where(TrackedProduct.user_id == user_id)
        )
        return int(result.scalar_one())

    async def get_by_user_and_url(self, user_id: int, canonical_url: str) -> TrackedProduct | None:
        result = await self.session.execute(
            select(TrackedProduct).where(
                and_(
                    TrackedProduct.user_id == user_id,
                    TrackedProduct.canonical_url == canonical_url,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        user_id: int,
        platform: str,
        title: str,
        original_url: str,
        canonical_url: str,
        affiliate_url: str | None,
        image_url: str | None,
        current_price: Decimal | None,
        original_price: Decimal | None,
        discount_percent: Decimal | None,
        is_available: bool,
        check_interval_minutes: int,
    ) -> TrackedProduct:
        now = datetime.utcnow()
        tracked = TrackedProduct(
            user_id=user_id,
            platform=platform,
            title=title,
            original_url=original_url,
            canonical_url=canonical_url,
            affiliate_url=affiliate_url,
            image_url=image_url,
            current_price=current_price,
            original_price=original_price,
            discount_percent=discount_percent,
            is_available=is_available,
            lowest_price=current_price,
            highest_price=current_price,
            last_checked_at=now,
            next_check_at=now + timedelta(minutes=check_interval_minutes),
            check_interval_minutes=check_interval_minutes,
            status=ProductStatus.ACTIVE.value,
        )
        self.session.add(tracked)
        await self.session.flush()
        return tracked

    async def get_by_id(self, tracked_product_id: int) -> TrackedProduct | None:
        result = await self.session.execute(select(TrackedProduct).where(TrackedProduct.id == tracked_product_id))
        return result.scalar_one_or_none()

    async def get_by_id_with_user(self, tracked_product_id: int) -> TrackedProduct | None:
        result = await self.session.execute(
            select(TrackedProduct)
            .options(selectinload(TrackedProduct.user))
            .where(TrackedProduct.id == tracked_product_id)
        )
        return result.scalar_one_or_none()

    async def list_user_products(self, user_id: int, limit: int = 50) -> list[TrackedProduct]:
        result = await self.session.execute(
            select(TrackedProduct)
            .where(TrackedProduct.user_id == user_id)
            .order_by(TrackedProduct.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def stop_tracking(self, tracked_product_id: int, user_id: int) -> bool:
        result = await self.session.execute(
            update(TrackedProduct)
            .where(
                and_(
                    TrackedProduct.id == tracked_product_id,
                    TrackedProduct.user_id == user_id,
                    TrackedProduct.status == ProductStatus.ACTIVE.value,
                )
            )
            .values(status=ProductStatus.PAUSED.value)
            .returning(TrackedProduct.id)
        )
        return result.scalar_one_or_none() is not None

    async def list_due_products(self, now: datetime, limit: int = 500) -> list[TrackedProduct]:
        result = await self.session.execute(
            select(TrackedProduct)
            .where(
                and_(
                    TrackedProduct.status == ProductStatus.ACTIVE.value,
                    TrackedProduct.next_check_at.is_not(None),
                    TrackedProduct.next_check_at <= now,
                )
            )
            .order_by(TrackedProduct.next_check_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_snapshot(
        self,
        tracked: TrackedProduct,
        *,
        title: str,
        image_url: str | None,
        current_price: Decimal | None,
        original_price: Decimal | None,
        discount_percent: Decimal | None,
        is_available: bool,
        next_check_at: datetime,
        strategy: str,
    ) -> None:
        now = datetime.utcnow()
        tracked.title = title
        tracked.image_url = image_url
        tracked.original_price = original_price
        tracked.discount_percent = discount_percent
        tracked.is_available = is_available
        tracked.last_checked_at = now
        tracked.next_check_at = next_check_at

        if current_price is not None:
            tracked.current_price = current_price
            low_candidates = [value for value in (tracked.lowest_price, current_price) if value is not None]
            high_candidates = [value for value in (tracked.highest_price, current_price) if value is not None]
            tracked.lowest_price = min(low_candidates) if low_candidates else current_price
            tracked.highest_price = max(high_candidates) if high_candidates else current_price

    async def refresh_next_check(self, tracked: TrackedProduct, next_check_at: datetime) -> None:
        tracked.next_check_at = next_check_at
        tracked.last_checked_at = datetime.utcnow()

    async def count_active(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(TrackedProduct).where(TrackedProduct.status == ProductStatus.ACTIVE.value)
        )
        return int(result.scalar_one())

    async def count_paused(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(TrackedProduct).where(TrackedProduct.status == ProductStatus.PAUSED.value)
        )
        return int(result.scalar_one())

    async def top_platforms(self, limit: int = 10) -> list[tuple[str, int]]:
        result = await self.session.execute(
            select(TrackedProduct.platform, func.count(TrackedProduct.id))
            .group_by(TrackedProduct.platform)
            .order_by(func.count(TrackedProduct.id).desc())
            .limit(limit)
        )
        return [(row[0], int(row[1])) for row in result.all()]
