from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BIGINT, Boolean, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import Platform, ProductStatus
from app.database.base import Base, TimestampMixin


class TrackedProduct(Base, TimestampMixin):
    __tablename__ = "tracked_products"
    __table_args__ = (
        UniqueConstraint("user_id", "canonical_url", name="uq_user_canonical_url"),
        Index("ix_tracked_products_next_check", "next_check_at", "status"),
        Index("ix_tracked_products_platform", "platform"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False, default=Platform.UNKNOWN.value)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    affiliate_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)

    current_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    original_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    discount_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    lowest_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    highest_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=ProductStatus.ACTIVE.value, nullable=False)

    check_interval_minutes: Mapped[int] = mapped_column(BIGINT, default=30, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="tracked_products")
    price_history = relationship("PriceHistory", back_populates="tracked_product", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="tracked_product", cascade="all, delete-orphan")
    affiliate_records = relationship("AffiliateLink", back_populates="tracked_product", cascade="all, delete-orphan")
