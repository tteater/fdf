from __future__ import annotations

from app.core.enums import Platform
from app.scrapers.platforms.common import SelectorScraper, SelectorSet


class MeeshoScraper(SelectorScraper):
    platform = Platform.MEESHO
    domains = ("meesho.com",)
    product_path_patterns = (r"/products?/",)
    selectors = SelectorSet(
        title=["h1", "meta[property='og:title']"],
        current_price=["h4", "span[data-testid='pdt-price']", "meta[property='product:price:amount']"],
        original_price=["h6", "span[data-testid='pdt-mrp']"],
        discount=["span[data-testid='pdt-discount']", "span"],
        image=[("img", "src"), ("meta[property='og:image']", "content")],
        availability=["div", "span"],
    )
