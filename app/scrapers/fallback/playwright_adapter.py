from __future__ import annotations

from app.core.exceptions import ScrapeError
from app.core.settings import Settings


class PlaywrightAdapter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def fetch(self, url: str) -> str:
        if not self.settings.playwright_enabled:
            raise ScrapeError("Playwright fallback is disabled")

        try:
            from playwright.async_api import async_playwright
        except Exception as exc:  # noqa: BLE001
            raise ScrapeError("Playwright dependency unavailable") from exc

        proxy_config = {"server": self.settings.proxy_url} if self.settings.proxy_url else None

        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True, proxy=proxy_config)
                context = await browser.new_context(user_agent=self.settings.user_agent)
                page = await context.new_page()
                response = await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                if response and response.status >= 400:
                    raise ScrapeError(f"Playwright got status={response.status}")
                await page.wait_for_timeout(2000)
                html = await page.content()
                await context.close()
                await browser.close()
                if not html:
                    raise ScrapeError("Playwright returned empty content")
                return html
        except Exception as exc:  # noqa: BLE001
            raise ScrapeError(f"Playwright fetch failed: {exc}") from exc
