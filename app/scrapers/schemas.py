from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class ProductSnapshot:
    title: str
    current_price: Decimal | None
    original_price: Decimal | None
    discount_percent: Decimal | None
    image_url: str | None
    is_available: bool
    canonical_url: str
    raw_html: str | None = None
