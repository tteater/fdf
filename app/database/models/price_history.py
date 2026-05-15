from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (
        Index("ix_price_history_product_checked", "tracked_product_id", "checked_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tracked_product_id: Mapped[int] = mapped_column(ForeignKey("tracked_products.id", ondelete="CASCADE"), nullable=False)

    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    original_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    discount_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    is_available: Mapped[bool] = mapped_column(default=True, nullable=False)
    scrape_strategy: Mapped[str] = mapped_column(String(32), nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    tracked_product = relationship("TrackedProduct", back_populates="price_history")
