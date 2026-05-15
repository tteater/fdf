from app.utils.urls import extract_urls, normalize_url


def test_extract_urls() -> None:
    text = "Check this https://www.amazon.in/dp/B0TEST123 and this"
    urls = extract_urls(text)
    assert urls == ["https://www.amazon.in/dp/B0TEST123"]


def test_normalize_url_removes_utm() -> None:
    url = "https://www.amazon.in/dp/B0TEST123/?utm_source=abc&tag=xyz"
    normalized = normalize_url(url)
    assert "utm_source" not in normalized
    assert "tag=xyz" in normalized
