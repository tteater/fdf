from __future__ import annotations

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.settings import Settings
from app.database.repositories import AdminLogRepository

logger = get_logger(__name__)


class AdminMonitorService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.bot = Bot(token=settings.admin_bot_token)

    async def close(self) -> None:
        await self.bot.session.close()

    async def log_event(
        self,
        session: AsyncSession,
        *,
        level: str,
        event: str,
        message: str,
        payload: dict | None = None,
        notify_admin: bool = False,
    ) -> None:
        repo = AdminLogRepository(session)
        await repo.create(level=level, event=event, message=message, payload=payload)

        normalized = level.lower()
        if normalized == "error":
            logger.error(message, event=event, payload=payload)
        elif normalized == "warning":
            logger.warning(message, event=event, payload=payload)
        else:
            logger.info(message, event=event, payload=payload)

        if notify_admin:
            await self.send_admin_message(level=level, event=event, message=message, payload=payload)

    async def send_admin_message(
        self,
        *,
        level: str,
        event: str,
        message: str,
        payload: dict | None = None,
    ) -> None:
        payload_summary = f"\nPayload: {payload}" if payload else ""
        text = (
            f"🛠 Admin Alert\n"
            f"Level: {level.upper()}\n"
            f"Event: {event}\n"
            f"Message: {message}"
            f"{payload_summary}"
        )
        try:
            await self.bot.send_message(self.settings.admin_chat_id, text)
        except Exception as exc:  # noqa: BLE001
            logger.exception("admin_message_send_failed", error=str(exc), event=event)
