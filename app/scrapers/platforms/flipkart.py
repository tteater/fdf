from __future__ import annotations

from app.core.enums import Platform
from app.scrapers.platforms.common import SelectorScraper, SelectorSet


class FlipkartScraper(SelectorScraper):
    platform = Platform.FLIPKART
    domains = ("flipkart.com",)
    product_path_patterns = (r"/p/",)
    selectors = SelectorSet(
        title=["span.B_NuCI", "h1.yhB1nd", "meta[property='og:title']"],
        current_price=["div._30jeq3", "div.Nx9bqj.CxhGGd", "meta[property='product:price:amount']"],
        original_price=["div._3I9_wc", "div.yRaY8j.A6+E6v"],
        discount=["div._3Ay6Sb span", "div.UkUFwK.WW8yVX span"],
        image=[("img._396cs4", "src"), ("img.DByuf4.IZexXJ.jLEJ7H", "src"), ("meta[property='og:image']", "content")],
        availability=["div._16FRp0", "div.Z8JjpR"],
    )
