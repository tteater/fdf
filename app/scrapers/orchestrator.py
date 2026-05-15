from __future__ import annotations

from dataclasses import dataclass

from app.core.enums import ScrapeStrategy
from app.core.exceptions import ScrapeError
from app.core.logging import get_logger
from app.core.settings import Settings
from app.scrapers.factory import get_scraper
from app.scrapers.fallback.playwright_adapter import PlaywrightAdapter
from app.scrapers.fallback.scrapling_adapter import ScraplingAdapter
from app.scrapers.normal_fetcher import NormalFetcher
from app.scrapers.schemas import ProductSnapshot

logger = get_logger(__name__)


@dataclass(slots=True)
class ScrapeResult:
    snapshot: ProductSnapshot
    strategy: ScrapeStrategy


class ScrapeOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.normal_fetcher = NormalFetcher(settings)
        self.scrapling_fetcher = ScraplingAdapter()
        self.playwright_fetcher = PlaywrightAdapter(settings)

    async def scrape(self, url: str) -> ScrapeResult:
        scraper = get_scraper(url)
        scraper.ensure_product_url(url)

        errors: list[tuple[ScrapeStrategy, str]] = []

        # primary: aiohttp + bs4
        try:
            html = await self.normal_fetcher.fetch(url)
            snapshot = scraper.parse(url, html)
            return ScrapeResult(snapshot=snapshot, strategy=ScrapeStrategy.NORMAL)
        except Exception as exc:  # noqa: BLE001
            logger.warning("scrape_primary_failed", url=url, error=str(exc))
            errors.append((ScrapeStrategy.NORMAL, str(exc)))

        # fallback 1: scrapling
        if self.settings.scrapling_enabled:
            try:
                html = await self.scrapling_fetcher.fetch(url)
                snapshot = scraper.parse(url, html)
                return ScrapeResult(snapshot=snapshot, strategy=ScrapeStrategy.SCRAPLING)
            except Exception as exc:  # noqa: BLE001
                logger.warning("scrape_scrapling_failed", url=url, error=str(exc))
                errors.append((ScrapeStrategy.SCRAPLING, str(exc)))

        # fallback 2: playwright
        if self.settings.playwright_enabled:
            try:
                html = await self.playwright_fetcher.fetch(url)
                snapshot = scraper.parse(url, html)
                return ScrapeResult(snapshot=snapshot, strategy=ScrapeStrategy.PLAYWRIGHT)
            except Exception as exc:  # noqa: BLE001
                logger.warning("scrape_playwright_failed", url=url, error=str(exc))
                errors.append((ScrapeStrategy.PLAYWRIGHT, str(exc)))

        detail = "; ".join(f"{strategy.value}: {reason}" for strategy, reason in errors)
        raise ScrapeError(f"All scraping strategies failed. {detail}")
