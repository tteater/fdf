from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.database.models import PriceHistory


def build_price_history_chart(product_title: str, points: list[PriceHistory], output_dir: Path) -> Path | None:
    series = [point for point in points if point.price is not None]
    if len(series) < 2:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"history_{series[0].tracked_product_id}_{int(datetime.utcnow().timestamp())}.png"

    x = [point.checked_at for point in reversed(series)]
    y = [float(point.price) for point in reversed(series)]

    plt.figure(figsize=(8, 4.5))
    plt.plot(x, y, marker="o", linewidth=2)
    plt.title(product_title[:80])
    plt.xlabel("Time")
    plt.ylabel("Price (INR)")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    return output_path
