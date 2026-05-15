from __future__ import annotations

import asyncio
from typing import Any

from app.core.exceptions import ScrapeError
from app.core.logging import get_logger

logger = get_logger(__name__)


class ScraplingAdapter:
    async def fetch(self, url: str) -> str:
        return await asyncio.to_thread(self._fetch_sync, url)

    def _fetch_sync(self, url: str) -> str:
        try:
            from scrapling.fetchers import Fetcher, StealthyFetcher
        except Exception as exc:  # noqa: BLE001
            raise ScrapeError("Scrapling dependency is unavailable") from exc

        page: Any | None = None
        fetch_errors: list[str] = []

        try:
            if hasattr(Fetcher, "get"):
                page = Fetcher.get(url)
            elif hasattr(Fetcher, "fetch"):
                page = Fetcher.fetch(url)
        except Exception as exc:  # noqa: BLE001
            fetch_errors.append(f"Fetcher failed: {exc}")

        if page is None:
            try:
                if hasattr(StealthyFetcher, "fetch"):
                    page = StealthyFetcher.fetch(url, headless=True, network_idle=True)
            except Exception as exc:  # noqa: BLE001
                fetch_errors.append(f"StealthyFetcher failed: {exc}")

        if page is None:
            error_text = "; ".join(fetch_errors) or "Unknown Scrapling error"
            raise ScrapeError(f"Scrapling fetch failed: {error_text}")

        html = self._extract_html(page)
        if not html:
            raise ScrapeError("Scrapling returned no parseable HTML")

        return html

    def _extract_html(self, page: Any) -> str:
        candidates = ["html", "html_content", "content", "raw", "text", "body"]
        for attr in candidates:
            value = getattr(page, attr, None)
            if isinstance(value, str) and value.strip():
                return value
            if callable(value):
                try:
                    result = value()
                    if isinstance(result, str) and result.strip():
                        return result
                except Exception:  # noqa: BLE001
                    continue

        as_str = str(page)
        if "<html" in as_str.lower():
            return as_str

        logger.warning("scrapling_unknown_page_object", type=type(page).__name__)
        return ""
