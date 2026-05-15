from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.settings import Settings
from app.database.session import create_engine_and_sessionmaker, create_redis
from app.scrapers import ScrapeOrchestrator
from app.services.admin_monitor_service import AdminMonitorService
from app.services.affiliate_service import AffiliateService
from app.services.price_monitor_service import PriceMonitorService
from app.services.product_list_service import ProductListService
from app.services.stats_service import StatsService
from app.services.tracking_service import TrackingService
from app.services.url_service import UrlService


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]
    redis: Redis
    tracking_service: TrackingService
    price_monitor_service: PriceMonitorService
    admin_monitor_service: AdminMonitorService
    product_list_service: ProductListService
    stats_service: StatsService
    started_at: datetime

    @classmethod
    def build(cls, settings: Settings) -> "AppContainer":
        engine, sessionmaker = create_engine_and_sessionmaker(settings)
        redis = create_redis(settings)

        url_service = UrlService()
        scraper = ScrapeOrchestrator(settings)
        affiliate = AffiliateService(settings)
        tracking_service = TrackingService(settings, url_service, scraper, affiliate)
        admin_monitor_service = AdminMonitorService(settings)
        stats_service = StatsService(started_at=datetime.now(timezone.utc))

        price_monitor_service = PriceMonitorService(
            settings=settings,
            sessionmaker=sessionmaker,
            tracking_service=tracking_service,
            admin_monitor=admin_monitor_service,
        )

        product_list_service = ProductListService()

        return cls(
            settings=settings,
            engine=engine,
            sessionmaker=sessionmaker,
            redis=redis,
            tracking_service=tracking_service,
            price_monitor_service=price_monitor_service,
            admin_monitor_service=admin_monitor_service,
            product_list_service=product_list_service,
            stats_service=stats_service,
            started_at=datetime.now(timezone.utc),
        )

    async def close(self) -> None:
        await self.price_monitor_service.close()
        await self.admin_monitor_service.close()
        await self.redis.aclose()
        await self.engine.dispose()
