from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bots.callbacks import ProductActionCallback


def price_alert_keyboard(product_id: int, buy_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Buy Now", url=buy_url)],
            [
                InlineKeyboardButton(
                    text="📉 View Price History",
                    callback_data=ProductActionCallback(action="history", product_id=product_id).pack(),
                ),
                InlineKeyboardButton(
                    text="🔄 Refresh Price",
                    callback_data=ProductActionCallback(action="refresh", product_id=product_id).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Stop Tracking",
                    callback_data=ProductActionCallback(action="stop", product_id=product_id).pack(),
                )
            ],
        ]
    )
