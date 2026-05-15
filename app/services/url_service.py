from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions import ValidationError
from app.utils.urls import expand_url, extract_urls, looks_like_shortened_url, normalize_url


@dataclass(slots=True)
class UrlProcessingResult:
    original_url: str
    expanded_url: str
    canonical_input_url: str


class UrlService:
    async def extract_and_prepare(self, text: str) -> UrlProcessingResult:
        urls = extract_urls(text)
        if not urls:
            raise ValidationError("Please send a valid product URL.")

        original = urls[0]
        expanded = await expand_url(original) if looks_like_shortened_url(original) else original

        try:
            normalized = normalize_url(expanded)
        except ValidationError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ValidationError(f"Invalid URL format: {exc}") from exc

        return UrlProcessingResult(original_url=original, expanded_url=expanded, canonical_input_url=normalized)
