from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.container import AppContainer
from app.core.logging import get_logger
from app.handlers.admin import router as admin_router
from app.middlewares.db_session import DatabaseSessionMiddleware

logger = get_logger(__name__)


async def run_admin_bot(container: AppContainer) -> None:
    bot = Bot(
        token=container.settings.admin_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(DatabaseSessionMiddleware(container.sessionmaker))
    dp.include_router(admin_router)

    logger.info("admin_bot_started")
    try:
        await dp.start_polling(
            bot,
            settings=container.settings,
            stats_service=container.stats_service,
        )
    finally:
        await bot.session.close()
