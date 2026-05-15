from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_type", "user_id", "notification_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tracked_product_id: Mapped[int] = mapped_column(ForeignKey("tracked_products.id", ondelete="CASCADE"), nullable=False)

    notification_type: Mapped[str] = mapped_column(String(32), nullable=False)
    old_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    new_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    telegram_message_id: Mapped[int | None] = mapped_column(nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tracked_product = relationship("TrackedProduct", back_populates="notifications")
