from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class ProductActionCallback(CallbackData, prefix="prd"):
    action: str
    product_id: int
