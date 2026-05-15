from __future__ import annotations

import asyncio

from app.bots.admin_bot import run_admin_bot
from app.core.container import AppContainer
from app.core.logging import configure_logging
from app.core.settings import get_settings


async def _main() -> None:
    settings = get_settings()
    configure_logging(settings)
    container = AppContainer.build(settings)
    try:
        await run_admin_bot(container)
    finally:
        await container.close()


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
