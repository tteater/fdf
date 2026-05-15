from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlunparse

from bs4 import BeautifulSoup

from app.core.exceptions import ScrapeError
from app.scrapers.base import BaseScraper
from app.scrapers.schemas import ProductSnapshot


@dataclass(slots=True)
class SelectorSet:
    title: list[str]
    current_price: list[str]
    original_price: list[str]
    discount: list[str]
    image: list[tuple[str, str]]
    availability: list[str]


class SelectorScraper(BaseScraper):
    selectors: SelectorSet

    def parse(self, url: str, html: str) -> ProductSnapshot:
        soup = BeautifulSoup(html, "lxml")

        title = self._extract_first_text(soup, self.selectors.title)
        if not title:
            raise ScrapeError("Missing title")

        current_price_raw = self._extract_first_text(soup, self.selectors.current_price)
        original_price_raw = self._extract_first_text(soup, self.selectors.original_price)
        discount_raw = self._extract_first_text(soup, self.selectors.discount)

        image_url = self._extract_first_attr(soup, self.selectors.image)

        availability = True
        for selector in self.selectors.availability:
            node = soup.select_one(selector)
            if not node:
                continue
            text = node.get_text(" ", strip=True).lower()
            if "out of stock" in text or "sold out" in text or "currently unavailable" in text:
                availability = False
                break

        canonical_url = self._canonicalize_url(url)
        snapshot = ProductSnapshot(
            title=title,
            current_price=self._parse_rupee(current_price_raw),
            original_price=self._parse_rupee(original_price_raw),
            discount_percent=self._parse_discount(discount_raw),
            image_url=image_url,
            is_available=availability,
            canonical_url=canonical_url,
            raw_html=html,
        )
        return self._basic_validate(snapshot)

    def _canonicalize_url(self, url: str) -> str:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
