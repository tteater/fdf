from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import aiohttp

from app.core.enums import AffiliateStatus
from app.core.logging import get_logger
from app.core.retry import with_retry
from app.core.settings import Settings

logger = get_logger(__name__)


@dataclass(slots=True)
class AffiliateConversionResult:
    status: AffiliateStatus
    affiliate_url: str | None
    message: str | None
    payload: dict | None


def _is_valid_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value.strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


class AffiliateService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def convert(self, product_url: str) -> AffiliateConversionResult:
        if not self.settings.earnkaro_api_token:
            return AffiliateConversionResult(
                status=AffiliateStatus.FAILED,
                affiliate_url=None,
                message="EarnKaro token is missing",
                payload=None,
            )

        async def _request() -> AffiliateConversionResult:
            timeout = aiohttp.ClientTimeout(total=self.settings.http_timeout_seconds)
            headers = {
                "Authorization": f"Bearer {self.settings.earnkaro_api_token}",
                "Content-Type": "application/json",
            }
            body = {"deal": product_url, "convert_option": "convert_only"}

            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.post(self.settings.earnkaro_base_url, json=body) as response:
                    text = await response.text()
                    payload: dict | None

                    try:
                        payload = await response.json(content_type=None)
                    except Exception:
                        payload = {"raw": text}

                    if response.status == 401:
                        return AffiliateConversionResult(AffiliateStatus.UNAUTHORIZED, None, "Please authenticate", payload)

                    if response.status == 429 or "Too many requests" in text:
                        return AffiliateConversionResult(AffiliateStatus.RATE_LIMITED, None, "Too many requests from this API key", payload)

                    if payload and payload.get("success") == 1 and payload.get("data"):
                        candidate = str(payload["data"]).strip()
                        if _is_valid_http_url(candidate):
                            return AffiliateConversionResult(AffiliateStatus.SUCCESS, candidate, None, payload)
                        return AffiliateConversionResult(
                            AffiliateStatus.UNSUPPORTED,
                            None,
                            candidate,  # e.g. "We could not locate an affiliate URL..."
                            payload,
                        )

                    if payload and payload.get("error") == 1:
                        message = str(payload.get("message", "Affiliate conversion failed"))
                        status = AffiliateStatus.UNSUPPORTED if "unsupported" in message.lower() else AffiliateStatus.FAILED
                        return AffiliateConversionResult(status, None, message, payload)

                    return AffiliateConversionResult(AffiliateStatus.FAILED, None, "Unexpected EarnKaro response", payload)

        try:
            result = await with_retry(_request, retries=self.settings.max_retries, exception_types=(aiohttp.ClientError, TimeoutError))
            logger.info("affiliate_conversion_complete", status=result.status.value, url=product_url)
            return result
        except Exception as exc:
            logger.exception("affiliate_conversion_exception", error=str(exc), url=product_url)
            return AffiliateConversionResult(AffiliateStatus.FAILED, None, str(exc), None)
