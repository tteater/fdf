from __future__ import annotations

from dataclasses import dataclass

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
                    payload: dict | None = None

                    try:
                        payload = await response.json(content_type=None)
                    except Exception:  # noqa: BLE001
                        payload = {"raw": text}

                    if response.status == 401:
                        return AffiliateConversionResult(
                            status=AffiliateStatus.UNAUTHORIZED,
                            affiliate_url=None,
                            message="Please authenticate",
                            payload=payload,
                        )

                    if response.status == 429 or "Too many requests" in text:
                        return AffiliateConversionResult(
                            status=AffiliateStatus.RATE_LIMITED,
                            affiliate_url=None,
                            message="Too many requests from this API key",
                            payload=payload,
                        )

                    if payload and payload.get("success") == 1 and payload.get("data"):
                        return AffiliateConversionResult(
                            status=AffiliateStatus.SUCCESS,
                            affiliate_url=str(payload["data"]),
                            message=None,
                            payload=payload,
                        )

                    if payload and payload.get("error") == 1:
                        message = str(payload.get("message", "Affiliate conversion failed"))
                        status = AffiliateStatus.UNSUPPORTED if "unsupported" in message.lower() else AffiliateStatus.FAILED
                        return AffiliateConversionResult(
                            status=status,
                            affiliate_url=None,
                            message=message,
                            payload=payload,
                        )

                    return AffiliateConversionResult(
                        status=AffiliateStatus.FAILED,
                        affiliate_url=None,
                        message="Unexpected EarnKaro response",
                        payload=payload,
                    )

        try:
            result = await with_retry(_request, retries=self.settings.max_retries, exception_types=(aiohttp.ClientError, TimeoutError))
            logger.info("affiliate_conversion_complete", status=result.status.value, url=product_url)
            return result
        except Exception as exc:  # noqa: BLE001
            logger.exception("affiliate_conversion_exception", error=str(exc), url=product_url)
            return AffiliateConversionResult(
                status=AffiliateStatus.FAILED,
                affiliate_url=None,
                message=str(exc),
                payload=None,
            )
