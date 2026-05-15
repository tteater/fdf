from __future__ import annotations

from pathlib import Path

from aiogram import F, Router
from aiogram.types import FSInputFile, Message
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.keyboards import price_alert_keyboard
from app.core.exceptions import (
    DuplicateTrackingError,
    ProductUrlError,
    ScrapeError,
    UnsupportedPlatformError,
    ValidationError,
)
from app.core.logging import get_logger
from app.services.admin_monitor_service import AdminMonitorService
from app.services.product_list_service import ProductListService
from app.services.tracking_service import TrackingService
from app.utils.formatters import build_tracking_started_message
from app.utils.urls import extract_urls

logger = get_logger(__name__)
router = Router(name="user_message_router")


@router.message(F.text)
async def handle_user_message(
    message: Message,
    session: AsyncSession,
    tracking_service: TrackingService,
    admin_monitor: AdminMonitorService,
    product_list_service: ProductListService,
) -> None:
    if not message.from_user or not message.text:
        return

    text = message.text.strip()
    if text.lower() in {"my products", "list", "wishlist"}:
        user = await tracking_service.ensure_user(session, message.from_user)
        summary = await product_list_service.list_for_user(session, user.id)
        await message.answer(summary)
        return

    if text.lower() in {"export", "export csv"}:
        user = await tracking_service.ensure_user(session, message.from_user)
        export_path = await product_list_service.export_csv(session, user.id, Path("artifacts/exports"))
        await message.answer_document(FSInputFile(export_path), caption="Your tracked products export")
        return

    urls = extract_urls(text)
    if not urls:
        await message.answer("Paste a product link to start automatic price tracking.")
        return

    async with ChatActionSender.typing(chat_id=message.chat.id, bot=message.bot):
        try:
            result = await tracking_service.start_tracking_from_message(session, message.from_user, text)

            tracked = result.tracked_product
            affiliate_ready = result.affiliate_result.affiliate_url is not None
            response = build_tracking_started_message(
                title=tracked.title,
                current_price=tracked.current_price,
                platform=tracked.platform,
                interval_minutes=tracked.check_interval_minutes,
                affiliate_ready=affiliate_ready,
            )

            buy_url = tracked.affiliate_url or tracked.canonical_url
            await message.answer(
                response,
                reply_markup=price_alert_keyboard(tracked.id, buy_url),
                disable_web_page_preview=False,
            )

            if result.is_new_user:
                await admin_monitor.log_event(
                    session,
                    level="info",
                    event="new_user_joined",
                    message="New user joined tracker",
                    payload={
                        "user_telegram_id": message.from_user.id,
                        "username": message.from_user.username,
                    },
                    notify_admin=True,
                )

            await admin_monitor.log_event(
                session,
                level="info",
                event="product_added",
                message="New product tracking created",
                payload={
                    "user_telegram_id": message.from_user.id,
                    "tracked_product_id": tracked.id,
                    "platform": tracked.platform,
                },
                notify_admin=False,
            )
        except DuplicateTrackingError:
            await message.answer("You are already tracking this product.")
        except ValidationError as exc:
            await message.answer(f"Invalid link: {exc}")
        except UnsupportedPlatformError:
            await message.answer("This website is not supported yet.")
        except ProductUrlError:
            await message.answer("Please send a direct product page link.")
        except ScrapeError as exc:
            await message.answer(f"I could not fetch that product right now. Reason: {exc}")
            await admin_monitor.log_event(
                session,
                level="error",
                event="scrape_failed",
                message="Scraping failed while starting tracking",
                payload={"user_telegram_id": message.from_user.id, "error": str(exc)},
                notify_admin=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("unexpected_message_handler_error", error=str(exc), user_id=message.from_user.id)
            await message.answer("Something went wrong while starting tracking. Please try again.")
            await admin_monitor.log_event(
                session,
                level="error",
                event="tracking_create_exception",
                message="Unexpected error while creating tracker",
                payload={"user_telegram_id": message.from_user.id, "error": str(exc)},
                notify_admin=True,
            )
