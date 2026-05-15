from __future__ import annotations

from app.core.enums import Platform
from app.scrapers.platforms.common import SelectorScraper, SelectorSet


class AmazonScraper(SelectorScraper):
    platform = Platform.AMAZON
    domains = ("amazon.in", "amzn.in")
    product_path_patterns = (r"/dp/", r"/gp/product/")
    selectors = SelectorSet(
        title=["#productTitle", "meta[property='og:title']"],
        current_price=[".a-price .a-offscreen", "#corePrice_feature_div .a-offscreen", "meta[property='product:price:amount']"],
        original_price=[".a-price.a-text-price .a-offscreen", ".priceBlockStrikePriceString"],
        discount=[".savingsPercentage", "#regularprice_savings .a-size-large"],
        image=[("#landingImage", "src"), ("#imgTagWrapperId img", "src"), ("meta[property='og:image']", "content")],
        availability=["#availability", "#outOfStock"],
    )
