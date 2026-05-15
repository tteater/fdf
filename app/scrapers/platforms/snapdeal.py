from __future__ import annotations

from app.core.enums import Platform
from app.scrapers.platforms.common import SelectorScraper, SelectorSet


class SnapdealScraper(SelectorScraper):
    platform = Platform.SNAPDEAL
    domains = ("snapdeal.com",)
    product_path_patterns = (r"/product/",)
    selectors = SelectorSet(
        title=["h1.pdp-e-i-head", "h1", "meta[property='og:title']"],
        current_price=["span.payBlkBig", "span.pdp-final-price", "meta[property='product:price:amount']"],
        original_price=["span.pdpCutPrice", "span.strike"],
        discount=["span.pdpDiscount", "span.percent-desc"],
        image=[("img.cloudzoom", "src"), ("meta[property='og:image']", "content")],
        availability=[".soldout-msg", ".notifyme"],
    )
