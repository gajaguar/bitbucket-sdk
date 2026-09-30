from __future__ import annotations

import asyncio
from time import monotonic
from time import sleep as _default_sleep
from typing import TYPE_CHECKING

from bitbucket.errors import PollTimeoutError

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from collections.abc import Callable


def poll_until_terminal[T](
    fetch: Callable[[], T],
    *,
    is_terminal: Callable[[T], bool],
    timeout: float = 60.0,
    interval: float = 1.0,
    sleep: Callable[[float], None] = _default_sleep,
) -> T:
    deadline = monotonic() + timeout
    while True:
        result = fetch()
        if is_terminal(result):
            return result
        if monotonic() >= deadline:
            message = f"Polling timed out after {timeout}s"
            raise PollTimeoutError(message)
        sleep(interval)


async def apoll_until_terminal[T](
    fetch: Callable[[], Awaitable[T]],
    *,
    is_terminal: Callable[[T], bool],
    timeout: float = 60.0,  # ruff: ignore[async-function-with-timeout]
    interval: float = 1.0,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> T:
    deadline = monotonic() + timeout
    while True:
        result = await fetch()
        if is_terminal(result):
            return result
        if monotonic() >= deadline:
            message = f"Polling timed out after {timeout}s"
            raise PollTimeoutError(message)
        await sleep(interval)
