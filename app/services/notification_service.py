from __future__ import annotations

from decimal import Decimal

from aiogram import Bot

from app.bots.keyboards import price_alert_keyboard
from app.core.enums import NotificationType
from app.core.logging import get_logger
from app.database.models import TrackedProduct
from app.database.repositories import NotificationRepository
from app.utils.formatters import build_price_drop_message

logger = get_logger(__name__)


class NotificationService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def send_price_drop(
        self,
        *,
        chat_id: int,
        tracked_product: TrackedProduct,
        old_price: Decimal | None,
        new_price: Decimal | None,
    ) -> int | None:
        target_url = tracked_product.affiliate_url or tracked_product.canonical_url
        text = build_price_drop_message(
            title=tracked_product.title,
            old_price=old_price,
            new_price=new_price,
            platform=tracked_product.platform,
            affiliate_url=target_url,
        )
        sent = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=price_alert_keyboard(tracked_product.id, target_url),
            disable_web_page_preview=False,
        )
        return sent.message_id

    async def send_back_in_stock(self, *, chat_id: int, tracked_product: TrackedProduct) -> int | None:
        target_url = tracked_product.affiliate_url or tracked_product.canonical_url
        text = (
            "✅ BACK IN STOCK\n\n"
            f"🛍 Product: {tracked_product.title}\n"
            f"🛒 Store: {tracked_product.platform.replace('_', ' ').title()}\n\n"
            f"🔗 Buy Now:\n{target_url}"
        )
        sent = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=price_alert_keyboard(tracked_product.id, target_url),
        )
        return sent.message_id

    async def send_major_discount(
        self,
        *,
        chat_id: int,
        tracked_product: TrackedProduct,
        old_price: Decimal | None,
        new_price: Decimal | None,
    ) -> int | None:
        target_url = tracked_product.affiliate_url or tracked_product.canonical_url
        text = (
            "🎯 MASSIVE DISCOUNT ALERT\n\n"
            f"🛍 Product: {tracked_product.title}\n"
            f"🏷 Old Price: {old_price}\n"
            f"💸 New Price: {new_price}\n"
            f"🛒 Store: {tracked_product.platform.replace('_', ' ').title()}\n\n"
            f"🔗 Buy Now:\n{target_url}"
        )
        sent = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=price_alert_keyboard(tracked_product.id, target_url),
        )
        return sent.message_id

    async def record_notification(
        self,
        notification_repo: NotificationRepository,
        *,
        user_id: int,
        tracked_product_id: int,
        notification_type: NotificationType,
        old_price: Decimal | None,
        new_price: Decimal | None,
        telegram_message_id: int | None,
    ) -> None:
        await notification_repo.create(
            user_id=user_id,
            tracked_product_id=tracked_product_id,
            notification_type=notification_type.value,
            old_price=old_price,
            new_price=new_price,
            telegram_message_id=telegram_message_id,
        )
        logger.info("notification_recorded", type=notification_type.value, product_id=tracked_product_id)
