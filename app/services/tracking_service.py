from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from aiogram.types import User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AffiliateStatus
from app.core.exceptions import DuplicateTrackingError
from app.core.logging import get_logger
from app.core.settings import Settings
from app.database.models import TrackedProduct, User
from app.database.repositories import (
    AffiliateRepository,
    PriceHistoryRepository,
    TrackedProductRepository,
    UserRepository,
)
from app.scrapers import ScrapeOrchestrator
from app.services.affiliate_service import AffiliateService, AffiliateConversionResult
from app.services.url_service import UrlService

logger = get_logger(__name__)


@dataclass(slots=True)
class TrackingCreateResult:
    user: User
    tracked_product: TrackedProduct
    affiliate_result: AffiliateConversionResult
    is_new_user: bool


class TrackingService:
    def __init__(self, settings: Settings, url_service: UrlService, scraper: ScrapeOrchestrator, affiliate: AffiliateService) -> None:
        self.settings = settings
        self.url_service = url_service
        self.scraper = scraper
        self.affiliate = affiliate

    async def ensure_user(self, session: AsyncSession, tg_user: TelegramUser) -> User:
        user_repo = UserRepository(session)
        user = await user_repo.create_or_update(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            language_code=tg_user.language_code,
            timezone=self.settings.timezone,
        )
        return user

    async def start_tracking_from_message(
        self,
        session: AsyncSession,
        tg_user: TelegramUser,
        text: str,
    ) -> TrackingCreateResult:
        url_data = await self.url_service.extract_and_prepare(text)
        scrape_result = await self.scraper.scrape(url_data.canonical_input_url)
        snapshot = scrape_result.snapshot

        user_repo = UserRepository(session)
        tracked_repo = TrackedProductRepository(session)
        price_repo = PriceHistoryRepository(session)
        affiliate_repo = AffiliateRepository(session)

        existing_user = await user_repo.get_by_telegram_id(tg_user.id)
        user = await user_repo.create_or_update(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            language_code=tg_user.language_code,
            timezone=self.settings.timezone,
        )

        tracked_count = await tracked_repo.count_for_user(user.id)
        if tracked_count >= self.settings.max_tracked_products_per_user:
            raise ValueError("You have reached your product tracking limit.")

        existing = await tracked_repo.get_by_user_and_url(user.id, snapshot.canonical_url)
        if existing is not None:
            raise DuplicateTrackingError("This product is already being tracked.")

        affiliate_result = await self.affiliate.convert(snapshot.canonical_url)
        affiliate_url = affiliate_result.affiliate_url or snapshot.canonical_url

        tracked = await tracked_repo.create(
            user_id=user.id,
            platform=self.scraper_platform(snapshot.canonical_url),
            title=snapshot.title,
            original_url=url_data.original_url,
            canonical_url=snapshot.canonical_url,
            affiliate_url=affiliate_url,
            image_url=snapshot.image_url,
            current_price=snapshot.current_price,
            original_price=snapshot.original_price,
            discount_percent=snapshot.discount_percent,
            is_available=snapshot.is_available,
            check_interval_minutes=self.settings.check_interval_minutes,
        )

        await price_repo.create(
            tracked_product_id=tracked.id,
            price=snapshot.current_price,
            original_price=snapshot.original_price,
            discount_percent=snapshot.discount_percent,
            is_available=snapshot.is_available,
            scrape_strategy=scrape_result.strategy.value,
            checked_at=datetime.utcnow(),
        )

        await affiliate_repo.create_record(
            tracked_product_id=tracked.id,
            original_url=snapshot.canonical_url,
            affiliate_url=affiliate_result.affiliate_url,
            status=affiliate_result.status.value,
            error_message=affiliate_result.message,
            response_payload=affiliate_result.payload,
        )

        logger.info(
            "tracking_created",
            user_id=user.id,
            tracked_product_id=tracked.id,
            platform=tracked.platform,
            strategy=scrape_result.strategy.value,
            affiliate_status=affiliate_result.status.value,
        )

        return TrackingCreateResult(
            user=user,
            tracked_product=tracked,
            affiliate_result=affiliate_result,
            is_new_user=existing_user is None,
        )

    async def refresh_product(self, session: AsyncSession, tracked: TrackedProduct) -> tuple[TrackedProduct, Decimal | None, bool]:
        scrape_result = await self.scraper.scrape(tracked.canonical_url)
        snapshot = scrape_result.snapshot

        tracked_repo = TrackedProductRepository(session)
        price_repo = PriceHistoryRepository(session)

        old_price = tracked.current_price
        old_availability = tracked.is_available

        await tracked_repo.update_snapshot(
            tracked,
            title=snapshot.title,
            image_url=snapshot.image_url,
            current_price=snapshot.current_price,
            original_price=snapshot.original_price,
            discount_percent=snapshot.discount_percent,
            is_available=snapshot.is_available,
            next_check_at=datetime.utcnow() + timedelta(minutes=tracked.check_interval_minutes),
            strategy=scrape_result.strategy.value,
        )

        await price_repo.create(
            tracked_product_id=tracked.id,
            price=snapshot.current_price,
            original_price=snapshot.original_price,
            discount_percent=snapshot.discount_percent,
            is_available=snapshot.is_available,
            scrape_strategy=scrape_result.strategy.value,
            checked_at=datetime.utcnow(),
        )

        changed = (old_price != snapshot.current_price) or (old_availability != snapshot.is_available)
        return tracked, old_price, changed

    def scraper_platform(self, url: str) -> str:
        from app.scrapers.factory import get_scraper

        scraper = get_scraper(url)
        return scraper.platform.value
