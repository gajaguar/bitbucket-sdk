from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest

from bitbucket.aio._retry_transport import AsyncRetryTransport  # ruff: ignore[import-private-name]
from bitbucket.retry import NO_RETRY
from bitbucket.retry import CqsKind
from bitbucket.retry import RetryPolicy

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from collections.abc import Callable


class _StubTransport(httpx.AsyncBaseTransport):
    def __init__(self, responses: list[httpx.Response]) -> None:
        self._responses = list(responses)
        self.calls = 0

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        del request
        self.calls += 1
        return self._responses.pop(0)


def _request(kind: CqsKind) -> httpx.Request:
    return httpx.Request("GET", "https://api.bitbucket.org/2.0/thing", extensions={"bitbucket_cqs": kind})


async def _fail_if_called(_: float) -> None:  # ruff: ignore[unused-async]
    pytest.fail("should not sleep")


async def _no_sleep(_: float) -> None:  # ruff: ignore[unused-async]
    return None


def _spy_factory(
    closed: list[bool],
    original_close: Callable[[], Awaitable[None]],
) -> Callable[[], Awaitable[None]]:
    async def _spy_close() -> None:
        closed.append(True)
        await original_close()

    return _spy_close


async def test_async_retries_429_and_respects_retry_after() -> None:  # pylint: disable=gajaguar-test-no-blank-lines
    # fmt: off
    # Arrange
    stub = _StubTransport([httpx.Response(429, headers={"Retry-After": "0"}), httpx.Response(200)])
    delays: list[float] = []
    async def _record_sleep(delay: float) -> None:  # ruff: ignore[unused-async, blank-lines-before-nested-definition]
        delays.append(delay)
    transport = AsyncRetryTransport(stub, policy=RetryPolicy(max_attempts=3), sleep=_record_sleep)
    # Act
    response = await transport.handle_async_request(_request(CqsKind.QUERY))
    # Assert
    assert response.status_code == httpx.codes.OK
    assert stub.calls == 2
    assert delays == [0.0]
    # fmt: on


async def test_async_non_idempotent_command_skips_5xx_retry() -> None:
    # Arrange
    stub = _StubTransport([httpx.Response(500)])
    policy = RetryPolicy(max_attempts=3)
    transport = AsyncRetryTransport(stub, policy=policy, sleep=_fail_if_called)
    # Act
    response = await transport.handle_async_request(_request(CqsKind.NON_IDEMPOTENT_COMMAND))
    # Assert
    assert response.status_code == httpx.codes.INTERNAL_SERVER_ERROR
    assert stub.calls == 1


async def test_async_idempotent_command_retries_5xx() -> None:
    # Arrange
    stub = _StubTransport([httpx.Response(503), httpx.Response(200)])
    transport = AsyncRetryTransport(stub, policy=RetryPolicy(max_attempts=3), sleep=_no_sleep)
    # Act
    response = await transport.handle_async_request(_request(CqsKind.IDEMPOTENT_COMMAND))
    # Assert
    assert response.status_code == httpx.codes.OK
    assert stub.calls == 2


async def test_async_no_retry_policy_makes_exactly_one_request() -> None:
    # Arrange
    stub = _StubTransport([httpx.Response(429)])
    transport = AsyncRetryTransport(stub, policy=NO_RETRY, sleep=_fail_if_called)
    # Act
    response = await transport.handle_async_request(_request(CqsKind.QUERY))
    # Assert
    assert response.status_code == httpx.codes.TOO_MANY_REQUESTS
    assert stub.calls == 1


async def test_async_close_delegates_to_next_transport() -> None:
    # Arrange
    stub = _StubTransport([])
    transport = AsyncRetryTransport(stub, policy=NO_RETRY)
    closed: list[bool] = []
    stub.aclose = _spy_factory(closed, stub.aclose)  # type: ignore[method-assign]
    # Act
    await transport.aclose()
    # Assert
    assert closed == [True]
