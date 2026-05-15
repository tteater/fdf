from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import aiohttp

from app.core.exceptions import ValidationError

URL_PATTERN = re.compile(r"https?://[^\s<>()]+", re.IGNORECASE)
SHORTENER_DOMAINS = {
    "amzn.in",
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "rb.gy",
    "cutt.ly",
    "shorturl.at",
}


def extract_urls(text: str) -> list[str]:
    return [match.group(0).rstrip(".,)") for match in URL_PATTERN.finditer(text)]


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValidationError("Only HTTP/HTTPS URLs are supported")

    query_items = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=False) if not k.lower().startswith("utm_")]
    clean_query = urlencode(query_items)
    clean_path = re.sub(r"/+", "/", parsed.path).rstrip("/") or "/"

    return urlunparse((parsed.scheme, parsed.netloc.lower(), clean_path, "", clean_query, ""))


def looks_like_shortened_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host in SHORTENER_DOMAINS


async def expand_url(url: str, timeout_seconds: int = 12) -> str:
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url, allow_redirects=True) as response:
                return str(response.url)
    except Exception:
        return url
