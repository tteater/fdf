from __future__ import annotations

import asyncio

from app.core.container import AppContainer
from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.schedulers.runner import run_scheduler


async def _main() -> None:
    settings = get_settings()
    configure_logging(settings)
    container = AppContainer.build(settings)
    try:
        await run_scheduler(container)
    finally:
        await container.close()


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
