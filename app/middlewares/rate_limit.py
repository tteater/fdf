from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from redis.asyncio import Redis

from app.core.logging import get_logger
from app.core.settings import Settings
from app.services.admin_monitor_service import AdminMonitorService

logger = get_logger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, redis: Redis, settings: Settings, admin_monitor: AdminMonitorService | None = None) -> None:
        self.redis = redis
        self.settings = settings
        self.admin_monitor = admin_monitor

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        key = f"rate_limit:{user_id}"

        try:
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, self.settings.user_message_rate_window_seconds)
        except Exception as exc:  # noqa: BLE001
            logger.warning("rate_limit_backend_error", error=str(exc), user_id=user_id)
            return await handler(event, data)

        if count > self.settings.user_message_rate_limit:
            logger.warning("rate_limit_exceeded", user_id=user_id, count=count)
            if self.admin_monitor and count == self.settings.user_message_rate_limit + 1:
                await self.admin_monitor.send_admin_message(
                    level="warning",
                    event="suspicious_spam",
                    message="User exceeded message rate limit",
                    payload={"user_telegram_id": user_id, "count": count},
                )
            await event.answer("⛔ Too many messages. Please wait a minute and try again.")
            return None

        return await handler(event, data)
