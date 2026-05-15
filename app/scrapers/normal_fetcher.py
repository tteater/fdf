from __future__ import annotations

import asyncio
import random

import aiohttp

from app.core.exceptions import ScrapeError
from app.core.logging import get_logger
from app.core.retry import with_retry
from app.core.settings import Settings

logger = get_logger(__name__)


class NormalFetcher:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def fetch(self, url: str) -> str:
        timeout = aiohttp.ClientTimeout(total=self.settings.http_timeout_seconds)
        headers = {
            "User-Agent": self.settings.user_agent,
            "Accept-Language": "en-IN,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        connector = aiohttp.TCPConnector(ssl=False)
        proxy = self.settings.proxy_url

        async def _request() -> str:
            await asyncio.sleep(random.uniform(0.2, 1.2))
            async with aiohttp.ClientSession(timeout=timeout, connector=connector, headers=headers) as session:
                async with session.get(url, proxy=proxy, allow_redirects=True) as response:
                    if response.status >= 400:
                        raise ScrapeError(f"Primary scraper status={response.status}")
                    html = await response.text()
                    if not html.strip():
                        raise ScrapeError("Primary scraper returned empty response")
                    return html

        try:
            return await with_retry(
                _request,
                retries=self.settings.max_retries,
                exception_types=(ScrapeError, aiohttp.ClientError, asyncio.TimeoutError),
                base_delay=1.0,
                max_delay=6.0,
            )
        except asyncio.TimeoutError as exc:
            raise ScrapeError("Primary scraper timeout") from exc
        except aiohttp.ClientError as exc:
            raise ScrapeError(f"Primary scraper network error: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("primary_fetch_failed", url=url, error=str(exc))
            raise
