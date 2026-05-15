from __future__ import annotations

from collections.abc import AsyncGenerator

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.logging import get_logger
from app.core.settings import Settings

logger = get_logger(__name__)


def create_engine_and_sessionmaker(settings: Settings) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=20,
        max_overflow=40,
        echo=False,
    )
    sessionmaker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    return engine, sessionmaker


def create_redis(settings: Settings) -> Redis:
    return Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)


async def session_scope(sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:  # noqa: BLE001
            await session.rollback()
            raise


async def db_healthcheck(sessionmaker: async_sessionmaker[AsyncSession]) -> bool:
    try:
        async with sessionmaker() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001
        logger.exception("db_health_failed", error=str(exc))
        return False


async def redis_healthcheck(redis: Redis) -> bool:
    try:
        await redis.ping()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.exception("redis_health_failed", error=str(exc))
        return False
