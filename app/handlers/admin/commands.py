from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import Settings
from app.services.stats_service import StatsService

router = Router(name="admin_commands_router")


def _is_admin(settings: Settings, telegram_id: int) -> bool:
    return telegram_id in settings.parsed_admin_ids


@router.message(Command("stats"))
async def admin_stats(
    message: Message,
    session: AsyncSession,
    settings: Settings,
    stats_service: StatsService,
) -> None:
    if not message.from_user or not _is_admin(settings, message.from_user.id):
        await message.answer("Unauthorized")
        return

    data = await stats_service.dashboard(session)
    top_stores = "\n".join([f"- {name}: {count}" for name, count in data["top_stores"]]) or "- No data"
    affiliate_lines = "\n".join([f"- {k}: {v}" for k, v in data["affiliate_stats"].items()]) or "- No data"

    text = (
        "📊 Admin Dashboard\n\n"
        f"👥 Total Users: {data['total_users']}\n"
        f"📦 Active Trackers: {data['active_trackers']}\n"
        f"⚠️ Failed Tracker Jobs: {data['failed_trackers']}\n"
        f"⏸ Paused Trackers: {data['paused_trackers']}\n"
        f"⏱ Uptime (s): {data['uptime_seconds']}\n"
        f"🕸 Scraping Success Rate: {data['scraping_success_rate']}%\n\n"
        "🏬 Top Stores:\n"
        f"{top_stores}\n\n"
        "💰 Affiliate Conversion Stats:\n"
        f"{affiliate_lines}"
    )
    await message.answer(text)


@router.message(Command("uptime"))
async def admin_uptime(
    message: Message,
    session: AsyncSession,
    settings: Settings,
    stats_service: StatsService,
) -> None:
    if not message.from_user or not _is_admin(settings, message.from_user.id):
        await message.answer("Unauthorized")
        return

    data = await stats_service.dashboard(session)
    await message.answer(f"Uptime: {data['uptime_seconds']} seconds")
