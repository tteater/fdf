from __future__ import annotations

from pathlib import Path

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.callbacks import ProductActionCallback
from app.core.logging import get_logger
from app.database.repositories import PriceHistoryRepository, TrackedProductRepository
from app.services.tracking_service import TrackingService
from app.utils.charts import build_price_history_chart
from app.utils.formatters import format_inr

logger = get_logger(__name__)
router = Router(name="user_callback_router")


@router.callback_query(ProductActionCallback.filter())
async def handle_product_action(
    callback: CallbackQuery,
    callback_data: ProductActionCallback,
    session: AsyncSession,
    tracking_service: TrackingService,
) -> None:
    if not callback.from_user:
        await callback.answer("User missing", show_alert=True)
        return

    user = await tracking_service.ensure_user(session, callback.from_user)
    tracked_repo = TrackedProductRepository(session)

    tracked = await tracked_repo.get_by_id_with_user(callback_data.product_id)
    if not tracked or tracked.user_id != user.id:
        await callback.answer("Tracker not found", show_alert=True)
        return

    action = callback_data.action

    if action == "stop":
        stopped = await tracked_repo.stop_tracking(tracked.id, user.id)
        await callback.answer("Tracking stopped" if stopped else "Already paused", show_alert=False)
        if callback.message:
            await callback.message.answer("Tracking has been paused for this product.")
        return

    if action == "refresh":
        try:
            old_price = tracked.current_price
            refreshed, _, _ = await tracking_service.refresh_product(session, tracked)
            change_line = ""
            if old_price is not None and refreshed.current_price is not None:
                delta = refreshed.current_price - old_price
                if delta != 0:
                    change_line = f"\nChange: {format_inr(delta)}"

            text = (
                "🔄 Price Refreshed\n\n"
                f"🛍 {refreshed.title}\n"
                f"🏷 Current Price: {format_inr(refreshed.current_price)}"
                f"{change_line}"
            )
            if callback.message:
                await callback.message.answer(text)
            await callback.answer("Updated", show_alert=False)
        except Exception as exc:  # noqa: BLE001
            logger.exception("refresh_failed", product_id=tracked.id, error=str(exc))
            await callback.answer("Refresh failed right now", show_alert=True)
        return

    if action == "history":
        history_repo = PriceHistoryRepository(session)
        points = await history_repo.list_recent(tracked.id, limit=30)
        chart_path = build_price_history_chart(tracked.title, points, Path("artifacts/charts"))

        if chart_path and callback.message:
            await callback.message.answer_photo(FSInputFile(chart_path), caption=f"Price history for {tracked.title[:60]}")
            await callback.answer("History generated", show_alert=False)
        else:
            await callback.answer("Not enough history yet", show_alert=True)
        return

    await callback.answer("Unknown action", show_alert=True)
