from __future__ import annotations

from app.core.enums import Platform
from app.scrapers.platforms.common import SelectorScraper, SelectorSet


class AjioScraper(SelectorScraper):
    platform = Platform.AJIO
    domains = ("ajio.com",)
    product_path_patterns = (r"/p/",)
    selectors = SelectorSet(
        title=["h1.prod-name", "h1", "meta[property='og:title']"],
        current_price=["span.prod-sp", "span.price", "meta[property='product:price:amount']"],
        original_price=["div.prod-mrp span", "span.deleted-price"],
        discount=["span.discount", "div.discount-percent"],
        image=[("img.prod-image", "src"), ("meta[property='og:image']", "content")],
        availability=[".sold-out", ".out-of-stock"],
    )
