from __future__ import annotations

import asyncio
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.enums import JobStatus, NotificationType
from app.core.logging import get_logger
from app.core.settings import Settings
from app.database.models import User
from app.database.repositories import (
    FailedJobRepository,
    NotificationRepository,
    TrackedProductRepository,
)
from app.services.admin_monitor_service import AdminMonitorService
from app.services.notification_service import NotificationService
from app.services.tracking_service import TrackingService
from app.utils.formatters import format_inr

logger = get_logger(__name__)


@dataclass(slots=True)
class MonitorResult:
    processed: int
    price_drops: int
    stock_alerts: int
    failures: int


class PriceMonitorService:
    def __init__(
        self,
        *,
        settings: Settings,
        sessionmaker: async_sessionmaker[AsyncSession],
        tracking_service: TrackingService,
        admin_monitor: AdminMonitorService,
    ) -> None:
        self.settings = settings
        self.sessionmaker = sessionmaker
        self.tracking_service = tracking_service
        self.admin_monitor = admin_monitor
        self.user_bot = Bot(token=settings.telegram_bot_token)
        self.notification_service = NotificationService(self.user_bot)

    async def close(self) -> None:
        await self.user_bot.session.close()

    async def run_cycle(self) -> MonitorResult:
        now = datetime.utcnow()

        async with self.sessionmaker() as session:
            tracked_repo = TrackedProductRepository(session)
            due_products = await tracked_repo.list_due_products(now, limit=500)
            due_ids = [item.id for item in due_products]

        queue: asyncio.Queue[int] = asyncio.Queue()
        for product_id in due_ids:
            queue.put_nowait(product_id)

        processed = 0
        price_drops = 0
        stock_alerts = 0
        failures = 0
        counters_lock = asyncio.Lock()

        worker_count = min(20, max(1, len(due_ids)))

        async def worker() -> None:
            nonlocal processed, price_drops, stock_alerts, failures
            while True:
                try:
                    product_id = queue.get_nowait()
                except asyncio.QueueEmpty:
                    return

                try:
                    success, had_drop, had_stock = await self._process_single_product(product_id)
                    async with counters_lock:
                        if success:
                            processed += 1
                            price_drops += int(had_drop)
                            stock_alerts += int(had_stock)
                        else:
                            failures += 1
                finally:
                    queue.task_done()

        workers = [asyncio.create_task(worker()) for _ in range(worker_count)]
        if workers:
            await asyncio.gather(*workers)

        logger.info(
            "monitor_cycle_completed",
            processed=processed,
            price_drops=price_drops,
            stock_alerts=stock_alerts,
            failures=failures,
        )
        return MonitorResult(processed=processed, price_drops=price_drops, stock_alerts=stock_alerts, failures=failures)

    async def send_daily_summary(self) -> int:
        sent_count = 0
        async with self.sessionmaker() as session:
            tracked_repo = TrackedProductRepository(session)
            users = (await session.execute(select(User).where(User.is_active.is_(True)))).scalars().all()
            for user in users:
                products = await tracked_repo.list_user_products(user.id, limit=100)
                if not products:
                    continue
                lines = [f"📊 Daily Summary ({len(products)} products)"]
                for product in products[:10]:
                    lines.append(
                        f"• {product.title[:40]} | {product.platform.replace('_', ' ').title()} | "
                        f"{format_inr(product.current_price)}"
                    )
                if len(products) > 10:
                    lines.append(f"... and {len(products) - 10} more")

                await self.user_bot.send_message(user.telegram_id, "\n".join(lines))
                sent_count += 1

        return sent_count

    async def _process_single_product(self, tracked_product_id: int) -> tuple[bool, bool, bool]:
        async with self.sessionmaker() as session:
            tracked_repo = TrackedProductRepository(session)
            failed_repo = FailedJobRepository(session)
            notification_repo = NotificationRepository(session)

            tracked = await tracked_repo.get_by_id_with_user(tracked_product_id)
            if not tracked:
                return True, False, False

            had_price_drop = False
            had_stock_alert = False

            try:
                old_price = tracked.current_price
                old_availability = tracked.is_available

                await self.tracking_service.refresh_product(session, tracked)

                if self._should_notify_price_drop(old_price, tracked.current_price):
                    message_id = await self.notification_service.send_price_drop(
                        chat_id=tracked.user.telegram_id,
                        tracked_product=tracked,
                        old_price=old_price,
                        new_price=tracked.current_price,
                    )
                    await self.notification_service.record_notification(
                        notification_repo,
                        user_id=tracked.user_id,
                        tracked_product_id=tracked.id,
                        notification_type=NotificationType.PRICE_DROP,
                        old_price=old_price,
                        new_price=tracked.current_price,
                        telegram_message_id=message_id,
                    )
                    had_price_drop = True

                if (not old_availability) and tracked.is_available:
                    message_id = await self.notification_service.send_back_in_stock(
                        chat_id=tracked.user.telegram_id,
                        tracked_product=tracked,
                    )
                    await self.notification_service.record_notification(
                        notification_repo,
                        user_id=tracked.user_id,
                        tracked_product_id=tracked.id,
                        notification_type=NotificationType.BACK_IN_STOCK,
                        old_price=old_price,
                        new_price=tracked.current_price,
                        telegram_message_id=message_id,
                    )
                    had_stock_alert = True

                if self._is_massive_discount(old_price, tracked.current_price):
                    message_id = await self.notification_service.send_major_discount(
                        chat_id=tracked.user.telegram_id,
                        tracked_product=tracked,
                        old_price=old_price,
                        new_price=tracked.current_price,
                    )
                    await self.notification_service.record_notification(
                        notification_repo,
                        user_id=tracked.user_id,
                        tracked_product_id=tracked.id,
                        notification_type=NotificationType.MAJOR_DISCOUNT,
                        old_price=old_price,
                        new_price=tracked.current_price,
                        telegram_message_id=message_id,
                    )

                await session.commit()
                return True, had_price_drop, had_stock_alert
            except Exception as exc:  # noqa: BLE001
                next_retry_at = datetime.utcnow() + timedelta(minutes=5)
                await failed_repo.create(
                    job_name="price_monitor",
                    status=JobStatus.FAILED.value,
                    entity_id=str(tracked_product_id),
                    attempt=1,
                    error_message=str(exc),
                    traceback=traceback.format_exc(),
                    next_retry_at=next_retry_at,
                )

                await self.admin_monitor.log_event(
                    session,
                    level="error",
                    event="scraping_failed",
                    message="Price monitor failed for product",
                    payload={"product_id": tracked_product_id, "error": str(exc)},
                    notify_admin=True,
                )

                await session.commit()
                logger.exception("monitor_product_failed", product_id=tracked_product_id, error=str(exc))
                return False, False, False

    def _should_notify_price_drop(self, old_price: Decimal | None, new_price: Decimal | None) -> bool:
        if old_price is None or new_price is None:
            return False
        if new_price >= old_price:
            return False
        change = old_price - new_price
        return change >= Decimal("10")

    def _is_massive_discount(self, old_price: Decimal | None, new_price: Decimal | None) -> bool:
        if old_price is None or new_price is None or old_price <= 0:
            return False
        percent = ((old_price - new_price) / old_price) * Decimal("100")
        return percent >= Decimal("20")
