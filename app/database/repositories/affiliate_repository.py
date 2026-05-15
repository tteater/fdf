from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AffiliateLink
from app.database.repositories.base import BaseRepository


class AffiliateRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create_record(
        self,
        *,
        tracked_product_id: int,
        original_url: str,
        affiliate_url: str | None,
        status: str,
        error_message: str | None,
        response_payload: dict | None,
    ) -> AffiliateLink:
        record = AffiliateLink(
            tracked_product_id=tracked_product_id,
            original_url=original_url,
            affiliate_url=affiliate_url,
            status=status,
            error_message=error_message,
            response_payload=response_payload,
        )
        self.session.add(record)
        await self.session.flush()
        return record
