from __future__ import annotations

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.container import AppContainer
from app.core.logging import get_logger
from app.schedulers.jobs import run_daily_summary, run_infra_health_check, run_price_checks

logger = get_logger(__name__)


async def run_scheduler(container: AppContainer) -> None:
    scheduler = AsyncIOScheduler(timezone=container.settings.timezone)

    scheduler.add_job(
        run_price_checks,
        trigger=IntervalTrigger(minutes=container.settings.check_interval_minutes),
        kwargs={"service": container.price_monitor_service},
        max_instances=1,
        coalesce=True,
        id="price-check-job",
    )

    scheduler.add_job(
        run_daily_summary,
        trigger=CronTrigger(hour=21, minute=0),
        kwargs={"service": container.price_monitor_service},
        max_instances=1,
        coalesce=True,
        id="daily-summary-job",
    )

    scheduler.add_job(
        run_infra_health_check,
        trigger=IntervalTrigger(minutes=15),
        kwargs={"container": container},
        max_instances=1,
        coalesce=True,
        id="infra-health-job",
    )

    scheduler.start()
    logger.info("scheduler_started")

    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown(wait=False)
