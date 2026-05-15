from __future__ import annotations

from decimal import Decimal


def format_inr(value: Decimal | None) -> str:
    if value is None:
        return "N/A"
    quantized = value.quantize(Decimal("0.01"))
    parts = f"{quantized:,.2f}".split(".")
    if parts[1] == "00":
        return f"₹{parts[0]}"
    return f"₹{parts[0]}.{parts[1]}"


def build_tracking_started_message(
    *,
    title: str,
    current_price: Decimal | None,
    platform: str,
    interval_minutes: int,
    affiliate_ready: bool,
) -> str:
    smart_link_line = "Ready" if affiliate_ready else "Using original link"
    return (
        "✅ Tracking Started\n\n"
        f"🛍 Product: {title}\n"
        f"🏷 Current Price: {format_inr(current_price)}\n"
        "📉 Drop Alert Enabled\n"
        f"🛒 Store: {platform.replace('_', ' ').title()}\n"
        f"🔗 Smart Purchase Link: {smart_link_line}\n"
        f"⏰ Checking Every {interval_minutes} Minutes"
    )


def build_price_drop_message(
    *,
    title: str,
    old_price: Decimal | None,
    new_price: Decimal | None,
    platform: str,
    affiliate_url: str,
) -> str:
    savings = None
    if old_price is not None and new_price is not None:
        savings = old_price - new_price

    save_line = f"📉 You Save: {format_inr(savings)}\n" if savings and savings > 0 else ""

    return (
        "🔥 PRICE DROP ALERT\n\n"
        f"🛍 Product: {title}\n"
        f"🏷 Old Price: {format_inr(old_price)}\n"
        f"💸 New Price: {format_inr(new_price)}\n"
        f"{save_line}"
        f"🛒 Store: {platform.replace('_', ' ').title()}\n\n"
        "🔗 Buy Now:\n"
        f"{affiliate_url}"
    )
