from __future__ import annotations

from enum import Enum


class Platform(str, Enum):
    AMAZON = "amazon"
    FLIPKART = "flipkart"
    AJIO = "ajio"
    MYNTRA = "myntra"
    MEESHO = "meesho"
    NYKAA = "nykaa"
    RELIANCE_DIGITAL = "reliance_digital"
    CROMA = "croma"
    TATA_CLIQ = "tata_cliq"
    SNAPDEAL = "snapdeal"
    UNKNOWN = "unknown"


class ProductStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    REMOVED = "removed"


class NotificationType(str, Enum):
    PRICE_DROP = "price_drop"
    BACK_IN_STOCK = "back_in_stock"
    MAJOR_DISCOUNT = "major_discount"
    DAILY_SUMMARY = "daily_summary"


class JobStatus(str, Enum):
    FAILED = "failed"
    RETRIED = "retried"
    SUCCESS = "success"


class AffiliateStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    UNAUTHORIZED = "unauthorized"
    UNSUPPORTED = "unsupported"


class ScrapeStrategy(str, Enum):
    NORMAL = "normal"
    SCRAPLING = "scrapling"
    PLAYWRIGHT = "playwright"


class StockState(str, Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    UNKNOWN = "unknown"
