from __future__ import annotations

from time import monotonic
from time import sleep as _default_sleep
from typing import TYPE_CHECKING

from bitbucket.errors import PollTimeoutError

if TYPE_CHECKING:
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
