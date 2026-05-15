from __future__ import annotations

from app.core.enums import Platform
from app.scrapers.platforms.common import SelectorScraper, SelectorSet


class MyntraScraper(SelectorScraper):
    platform = Platform.MYNTRA
    domains = ("myntra.com",)
    product_path_patterns = (r"/buy", r"/\d+")
    selectors = SelectorSet(
        title=["h1.pdp-title", "h1", "meta[property='og:title']"],
        current_price=["span.pdp-price strong", "span.pdp-price", "meta[property='product:price:amount']"],
        original_price=["span.pdp-mrp s", "span.pdp-mrp"],
        discount=["span.pdp-discount", ".pdp-offers-labelMarkup"],
        image=[("img.image-grid-image", "src"), ("meta[property='og:image']", "content")],
        availability=[".pdp-outOfStock", ".notify-soldout"],
    )
