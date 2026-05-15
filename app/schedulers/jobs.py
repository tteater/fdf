from __future__ import annotations

import aiohttp

from app.core.container import AppContainer
from app.core.logging import get_logger
from app.database.session import db_healthcheck, redis_healthcheck
from app.services.price_monitor_service import PriceMonitorService

logger = get_logger(__name__)


async def run_price_checks(service: PriceMonitorService) -> None:
    try:
        result = await service.run_cycle()
        logger.info(
            "scheduled_price_check_done",
            processed=result.processed,
            price_drops=result.price_drops,
            stock_alerts=result.stock_alerts,
            failures=result.failures,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("scheduled_price_check_failed", error=str(exc))
        await service.admin_monitor.send_admin_message(
            level="error",
            event="scheduler_failure",
            message=f"Price check scheduler failed: {exc}",
        )


async def run_daily_summary(service: PriceMonitorService) -> None:
    try:
        sent = await service.send_daily_summary()
        logger.info("scheduled_daily_summary_done", sent=sent)
    except Exception as exc:  # noqa: BLE001
        logger.exception("scheduled_daily_summary_failed", error=str(exc))
        await service.admin_monitor.send_admin_message(
            level="error",
            event="scheduler_failure",
            message=f"Daily summary scheduler failed: {exc}",
        )


async def run_infra_health_check(container: AppContainer) -> None:
    db_ok = await db_healthcheck(container.sessionmaker)
    redis_ok = await redis_healthcheck(container.redis)

    if not db_ok:
        await container.admin_monitor_service.send_admin_message(
            level="error",
            event="db_issue",
            message="Database health check failed",
        )

    if not redis_ok:
        await container.admin_monitor_service.send_admin_message(
            level="error",
            event="server_offline",
            message="Redis health check failed",
        )

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        headers = {"Authorization": f"Bearer {container.settings.earnkaro_api_token}", "Content-Type": "application/json"}
        payload = {"deal": "https://www.amazon.in/dp/B0TEST123", "convert_option": "convert_only"}
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.post(container.settings.earnkaro_base_url, json=payload):
                pass
    except Exception as exc:  # noqa: BLE001
        await container.admin_monitor_service.send_admin_message(
            level="error",
            event="api_issue",
            message=f"EarnKaro API connectivity failed: {exc}",
        )
