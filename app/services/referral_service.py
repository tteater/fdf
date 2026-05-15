from __future__ import annotations

import secrets
import string

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User


class ReferralService:
    def _random_code(self, length: int = 8) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    async def ensure_referral_code(self, session: AsyncSession, user: User) -> str:
        if user.referral_code:
            return user.referral_code

        user.referral_code = self._random_code()
        await session.flush()
        return user.referral_code
