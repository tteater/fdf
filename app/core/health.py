from __future__ import annotations

from collections.abc import Awaitable, Callable

from app.core.logging import get_logger

logger = get_logger(__name__)


async def run_health_checks(checks: dict[str, Callable[[], Awaitable[bool]]]) -> dict[str, bool]:
    status: dict[str, bool] = {}
    for name, check in checks.items():
        try:
            status[name] = await check()
        except Exception as exc:  # noqa: BLE001
            logger.exception("health_check_failed", check=name, error=str(exc))
            status[name] = False
    return status
