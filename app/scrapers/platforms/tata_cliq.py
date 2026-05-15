from __future__ import annotations

from app.core.enums import Platform
from app.scrapers.platforms.common import SelectorScraper, SelectorSet


class TataCliqScraper(SelectorScraper):
    platform = Platform.TATA_CLIQ
    domains = ("tatacliq.com",)
    product_path_patterns = (r"/p-mp", r"/p-")
    selectors = SelectorSet(
        title=["h1.ProductDescription__title", "h1", "meta[property='og:title']"],
        current_price=["span.ProductDescription__priceHolder", "span._2xvKa", "meta[property='product:price:amount']"],
        original_price=["span.ProductDescription__originalPrice", "span._3f2Zx"],
        discount=["span.ProductDescription__discount", "span._3ee2X"],
        image=[("img.PDPMainProductImage__image", "src"), ("meta[property='og:image']", "content")],
        availability=[".ProductDescription__soldOut", ".out-of-stock"],
    )
