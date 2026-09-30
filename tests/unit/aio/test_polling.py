from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitbucket._polling import apoll_until_terminal  # ruff: ignore[import-private-name]
from bitbucket.errors import PollTimeoutError

if TYPE_CHECKING:
    from collections.abc import Callable


def _make_counter_fetch(counter: dict[str, int]) -> Callable[[], int]:
    def _fetch() -> int:
        counter["value"] += 1
        return counter["value"]

    return _fetch


async def _await_sync(value: Callable[[], int]) -> int:  # ruff: ignore[unused-async]
    return value()


async def _zero_sleep(_: float) -> None:  # ruff: ignore[unused-async]
    return None


async def test_apoll_until_terminal_returns_when_is_terminal_true() -> None:
    # Arrange
    counter = {"value": 0}
    fetch = _make_counter_fetch(counter)
    # Act
    result = await apoll_until_terminal(
        lambda: _await_sync(fetch), is_terminal=lambda value: value >= 2, timeout=10.0, interval=0.0
    )
    # Assert
    assert result == 2
    assert counter == {"value": 2}


async def test_apoll_until_terminal_raises_on_timeout() -> None:
    # Arrange
    counter = {"value": 0}
    fetch = _make_counter_fetch(counter)
    # Act
    with pytest.raises(PollTimeoutError, match="timed out"):
        await apoll_until_terminal(
            lambda: _await_sync(fetch),
            is_terminal=lambda _: False,
            timeout=0.0,
            interval=0.0,
            sleep=_zero_sleep,
        )
    # Assert
    assert counter == {"value": 1}
