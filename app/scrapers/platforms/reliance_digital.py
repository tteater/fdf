from __future__ import annotations

from app.core.enums import Platform
from app.scrapers.platforms.common import SelectorScraper, SelectorSet


class RelianceDigitalScraper(SelectorScraper):
    platform = Platform.RELIANCE_DIGITAL
    domains = ("reliancedigital.in",)
    product_path_patterns = (r"/product/",)
    selectors = SelectorSet(
        title=["h1.pdp__title", "h1", "meta[property='og:title']"],
        current_price=["span.pdp__priceSection__priceListText", "span._21Ahn-", "meta[property='product:price:amount']"],
        original_price=["span.pdp__priceSection__priceStrikeOff", "span.rdp__strike"],
        discount=["span.pdp__offerPercentage", "span.offer-percentage"],
        image=[("img.pdp__image", "src"), ("meta[property='og:image']", "content")],
        availability=[".pdp__availability", ".outOfStock"],
    )
