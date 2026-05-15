from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AffiliateLink, FailedJob, PriceHistory
from app.database.repositories import TrackedProductRepository, UserRepository


class StatsService:
    def __init__(self, started_at: datetime) -> None:
        self.started_at = started_at

    async def dashboard(self, session: AsyncSession) -> dict:
        user_repo = UserRepository(session)
        tracked_repo = TrackedProductRepository(session)

        total_users = await user_repo.count_users()
        active_trackers = await tracked_repo.count_active()
        paused_trackers = await tracked_repo.count_paused()

        scrape_total_result = await session.execute(select(func.count()).select_from(PriceHistory))
        scrape_total = int(scrape_total_result.scalar_one())
        failed_jobs_result = await session.execute(select(func.count()).select_from(FailedJob))
        failed_jobs = int(failed_jobs_result.scalar_one())

        scrape_success_rate = 100.0
        if scrape_total > 0:
            scrape_success_rate = max(0.0, ((scrape_total - failed_jobs) / scrape_total) * 100)

        top_stores = await tracked_repo.top_platforms(limit=5)

        affiliate_rows = await session.execute(
            select(AffiliateLink.status, func.count(AffiliateLink.id)).group_by(AffiliateLink.status)
        )
        affiliate_stats = {status: int(total) for status, total in affiliate_rows.all()}

        uptime_seconds = int((datetime.now(timezone.utc) - self.started_at).total_seconds())

        return {
            "total_users": total_users,
            "active_trackers": active_trackers,
            "failed_trackers": failed_jobs,
            "paused_trackers": paused_trackers,
            "uptime_seconds": uptime_seconds,
            "scraping_success_rate": round(scrape_success_rate, 2),
            "top_stores": top_stores,
            "affiliate_stats": affiliate_stats,
        }
