from __future__ import annotations

from app.core.enums import Platform
from app.scrapers.platforms.common import SelectorScraper, SelectorSet


class CromaScraper(SelectorScraper):
    platform = Platform.CROMA
    domains = ("croma.com",)
    product_path_patterns = (r"/p/",)
    selectors = SelectorSet(
        title=["h1.product-title", "h1", "meta[property='og:title']"],
        current_price=["span.amount", "span.new-price", "meta[property='product:price:amount']"],
        original_price=["span.old-price", "span.strike"],
        discount=["span.discount", "span.off"],
        image=[("img.product-image", "src"), ("meta[property='og:image']", "content")],
        availability=[".stock-status", ".out-of-stock"],
    )
