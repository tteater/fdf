from __future__ import annotations

import asyncio

from app.bots.admin_bot import run_admin_bot
from app.bots.user_bot import run_user_bot
from app.core.container import AppContainer
from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.schedulers.runner import run_scheduler


async def _main() -> None:
    settings = get_settings()
    configure_logging(settings)
    container = AppContainer.build(settings)

    user_task = asyncio.create_task(run_user_bot(container))
    admin_task = asyncio.create_task(run_admin_bot(container))
    scheduler_task = asyncio.create_task(run_scheduler(container))

    try:
        await asyncio.gather(user_task, admin_task, scheduler_task)
    finally:
        await container.close()


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
