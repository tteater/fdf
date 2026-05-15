from __future__ import annotations

import re
from abc import ABC, abstractmethod
from decimal import Decimal
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.core.enums import Platform
from app.core.exceptions import ProductUrlError, ScrapeError
from app.scrapers.schemas import ProductSnapshot


class BaseScraper(ABC):
    platform: Platform = Platform.UNKNOWN
    domains: tuple[str, ...] = ()
    product_path_patterns: tuple[str, ...] = ()

    def matches_domain(self, url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return any(domain in host for domain in self.domains)

    def is_product_url(self, url: str) -> bool:
        path = urlparse(url).path.lower()
        return any(re.search(pattern, path) for pattern in self.product_path_patterns)

    @abstractmethod
    def parse(self, url: str, html: str) -> ProductSnapshot:
        raise NotImplementedError

    def _extract_first_text(self, soup: BeautifulSoup, selectors: list[str]) -> str | None:
        for selector in selectors:
            node = soup.select_one(selector)
            if node and node.get_text(strip=True):
                return node.get_text(strip=True)
        return None

    def _extract_first_attr(self, soup: BeautifulSoup, selectors: list[tuple[str, str]]) -> str | None:
        for selector, attr in selectors:
            node = soup.select_one(selector)
            if node:
                value = node.get(attr)
                if value:
                    return str(value)
        return None

    def _parse_rupee(self, text: str | None) -> Decimal | None:
        if not text:
            return None
        cleaned = re.sub(r"[^0-9.,]", "", text).replace(",", "")
        if not cleaned:
            return None
        try:
            return Decimal(cleaned)
        except Exception:  # noqa: BLE001
            return None

    def _parse_discount(self, text: str | None) -> Decimal | None:
        if not text:
            return None
        match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
        if not match:
            return None
        try:
            return Decimal(match.group(1))
        except Exception:  # noqa: BLE001
            return None

    def _basic_validate(self, snapshot: ProductSnapshot) -> ProductSnapshot:
        if not snapshot.title:
            raise ScrapeError("Could not extract product title")
        return snapshot

    def ensure_product_url(self, url: str) -> None:
        if not self.is_product_url(url):
            raise ProductUrlError("This link doesn't look like a product page")
