from __future__ import annotations


class AppError(Exception):
    """Base application exception."""


class ValidationError(AppError):
    """Raised when user input is invalid."""


class UnsupportedPlatformError(AppError):
    """Raised when URL platform is not supported."""


class ProductUrlError(AppError):
    """Raised when URL does not represent a product page."""


class ScrapeError(AppError):
    """Raised when scraping fails."""


class AffiliateConversionError(AppError):
    """Raised when affiliate conversion fails."""


class DuplicateTrackingError(AppError):
    """Raised when a duplicate tracking request arrives."""


class RateLimitExceededError(AppError):
    """Raised when user hits throttling guard rails."""
