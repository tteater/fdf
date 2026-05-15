from __future__ import annotations

from decimal import Decimal

from app.database.models import TrackedProduct


class AffiliateAnalyticsService:
    def estimate_earning(
        self,
        product: TrackedProduct,
        *,
        estimated_conversion_rate: Decimal = Decimal("0.02"),
        commission_rate: Decimal = Decimal("0.04"),
    ) -> Decimal:
        if product.current_price is None:
            return Decimal("0")
        return product.current_price * estimated_conversion_rate * commission_rate
