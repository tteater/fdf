import pytest

from app.core.exceptions import UnsupportedPlatformError
from app.scrapers.factory import get_scraper


def test_detect_amazon_scraper() -> None:
    scraper = get_scraper("https://www.amazon.in/dp/B0TEST123")
    assert scraper.platform.value == "amazon"


def test_unsupported_platform() -> None:
    with pytest.raises(UnsupportedPlatformError):
        get_scraper("https://example.com/product/123")
