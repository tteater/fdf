from __future__ import annotations

from typing import Any, Awaitable, Callable, TypeVar

from tenacity import AsyncRetrying, RetryCallState, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.logging import get_logger

T = TypeVar("T")
logger = get_logger(__name__)


def _before_sleep(retry_state: RetryCallState) -> None:
    logger.warning(
        "retry_scheduled",
        fn=str(retry_state.fn),
        attempt=retry_state.attempt_number,
        exception=repr(retry_state.outcome.exception()) if retry_state.outcome else None,
    )


async def with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    retries: int,
    exception_types: tuple[type[Exception], ...] = (Exception,),
    base_delay: float = 1.0,
    max_delay: float = 20.0,
) -> T:
    async for attempt in AsyncRetrying(
        retry=retry_if_exception_type(exception_types),
        stop=stop_after_attempt(retries),
        wait=wait_exponential(multiplier=base_delay, min=base_delay, max=max_delay),
        before_sleep=_before_sleep,
        reraise=True,
    ):
        with attempt:
            return await operation()
    raise RuntimeError("Retry loop exited unexpectedly")
