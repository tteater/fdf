from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories import TrackedProductRepository
from app.utils.formatters import format_inr


class ProductListService:
    async def list_for_user(self, session: AsyncSession, user_id: int) -> str:
        repo = TrackedProductRepository(session)
        items = await repo.list_user_products(user_id, limit=100)
        if not items:
            return "You are not tracking any products yet."

        lines = ["📦 Your Tracked Products"]
        for item in items[:20]:
            lines.append(
                f"• {item.title[:50]} | {format_inr(item.current_price)} | {item.platform.replace('_', ' ').title()}"
            )
        if len(items) > 20:
            lines.append(f"... and {len(items) - 20} more")
        return "\n".join(lines)

    async def export_csv(self, session: AsyncSession, user_id: int, output_dir: Path) -> Path:
        repo = TrackedProductRepository(session)
        items = await repo.list_user_products(user_id, limit=500)

        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / f"tracked_products_{user_id}.csv"

        with file_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "title",
                    "platform",
                    "current_price",
                    "original_price",
                    "discount_percent",
                    "is_available",
                    "affiliate_url",
                    "created_at",
                ]
            )
            for item in items:
                writer.writerow(
                    [
                        item.title,
                        item.platform,
                        item.current_price,
                        item.original_price,
                        item.discount_percent,
                        item.is_available,
                        item.affiliate_url or item.canonical_url,
                        item.created_at.isoformat(),
                    ]
                )

        return file_path
