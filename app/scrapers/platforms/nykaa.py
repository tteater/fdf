from __future__ import annotations

from app.core.enums import Platform
from app.scrapers.platforms.common import SelectorScraper, SelectorSet


class NykaaScraper(SelectorScraper):
    platform = Platform.NYKAA
    domains = ("nykaa.com",)
    product_path_patterns = (r"/p/",)
    selectors = SelectorSet(
        title=["h1.css-1gc4x7i", "h1", "meta[property='og:title']"],
        current_price=["span.css-111z9ua", "span.css-0", "meta[property='product:price:amount']"],
        original_price=["span.css-17x46n5", "span.css-1jczs19"],
        discount=["span.css-rk3rbr", "span.css-1j33oxj"],
        image=[("img.css-11gn9r6", "src"), ("meta[property='og:image']", "content")],
        availability=[".css-1f5ta5v", ".css-18n4f4s"],
    )
