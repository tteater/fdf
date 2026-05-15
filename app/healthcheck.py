from __future__ import annotations

import asyncio

from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.database.session import create_engine_and_sessionmaker, create_redis, db_healthcheck, redis_healthcheck


async def _main() -> int:
    settings = get_settings()
    configure_logging(settings)

    engine, sessionmaker = create_engine_and_sessionmaker(settings)
    redis = create_redis(settings)

    db_ok = await db_healthcheck(sessionmaker)
    redis_ok = await redis_healthcheck(redis)

    await redis.aclose()
    await engine.dispose()

    if db_ok and redis_ok:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
