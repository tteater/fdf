from __future__ import annotations

from urllib.parse import urlparse

from app.core.exceptions import UnsupportedPlatformError
from app.scrapers.base import BaseScraper
from app.scrapers.platforms import (
    AjioScraper,
    AmazonScraper,
    CromaScraper,
    FlipkartScraper,
    MeeshoScraper,
    MyntraScraper,
    NykaaScraper,
    RelianceDigitalScraper,
    SnapdealScraper,
    TataCliqScraper,
)

SCRAPER_REGISTRY: list[BaseScraper] = [
    AmazonScraper(),
    FlipkartScraper(),
    AjioScraper(),
    MyntraScraper(),
    MeeshoScraper(),
    NykaaScraper(),
    RelianceDigitalScraper(),
    CromaScraper(),
    TataCliqScraper(),
    SnapdealScraper(),
]


def get_scraper(url: str) -> BaseScraper:
    host = urlparse(url).netloc.lower()
    for scraper in SCRAPER_REGISTRY:
        if scraper.matches_domain(url):
            return scraper
    raise UnsupportedPlatformError(f"Unsupported website: {host}")
