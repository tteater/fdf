from __future__ import annotations

from sqlalchemy import Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class AdminLog(Base, TimestampMixin):
    __tablename__ = "admin_logs"
    __table_args__ = (
        Index("ix_admin_logs_event", "event"),
        Index("ix_admin_logs_level", "level"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    event: Mapped[str] = mapped_column(String(128), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
