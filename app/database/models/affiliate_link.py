from __future__ import annotations

from sqlalchemy import ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class AffiliateLink(Base, TimestampMixin):
    __tablename__ = "affiliate_links"
    __table_args__ = (
        Index("ix_affiliate_links_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tracked_product_id: Mapped[int] = mapped_column(ForeignKey("tracked_products.id", ondelete="CASCADE"), nullable=False)
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    affiliate_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    response_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    tracked_product = relationship("TrackedProduct", back_populates="affiliate_records")
