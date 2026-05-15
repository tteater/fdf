from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.container import AppContainer
from app.core.logging import get_logger
from app.handlers.user import callback_router, message_router
from app.middlewares.db_session import DatabaseSessionMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware

logger = get_logger(__name__)


async def run_user_bot(container: AppContainer) -> None:
    bot = Bot(
        token=container.settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(DatabaseSessionMiddleware(container.sessionmaker))
    dp.callback_query.middleware(DatabaseSessionMiddleware(container.sessionmaker))
    dp.message.middleware(
        RateLimitMiddleware(
            container.redis,
            container.settings,
            admin_monitor=container.admin_monitor_service,
        )
    )

    dp.include_router(message_router)
    dp.include_router(callback_router)

    logger.info("user_bot_started")
    try:
        await dp.start_polling(
            bot,
            settings=container.settings,
            tracking_service=container.tracking_service,
            admin_monitor=container.admin_monitor_service,
            product_list_service=container.product_list_service,
        )
    finally:
        await bot.session.close()
