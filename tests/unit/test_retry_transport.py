from __future__ import annotations

import httpx
import pytest

from bitbucket._retry_transport import RetryTransport  # ruff: ignore[import-private-name]
from bitbucket.retry import NO_RETRY
from bitbucket.retry import CqsKind
from bitbucket.retry import RetryPolicy


class _StubTransport(httpx.BaseTransport):
    def __init__(self, responses: list[httpx.Response]) -> None:
        self._responses = list(responses)
        self.calls = 0

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        del request
        self.calls += 1
        return self._responses.pop(0)


def _request(kind: CqsKind) -> httpx.Request:
    return httpx.Request("GET", "https://api.bitbucket.org/2.0/thing", extensions={"bitbucket_cqs": kind})


def _fail_if_called(delay: float) -> None:
    del delay
    pytest.fail("should not sleep")


def test_retries_429_and_respects_retry_after() -> None:
    # Arrange
    stub = _StubTransport([httpx.Response(429, headers={"Retry-After": "0"}), httpx.Response(200)])
    delays: list[float] = []
    transport = RetryTransport(stub, policy=RetryPolicy(max_attempts=3), sleep=delays.append)
    # Act
    response = transport.handle_request(_request(CqsKind.QUERY))
    # Assert
    assert response.status_code == httpx.codes.OK
    assert stub.calls == 2
    assert delays == [0.0]


def test_non_idempotent_command_skips_5xx_retry() -> None:
    # Arrange
    stub = _StubTransport([httpx.Response(500)])
    policy = RetryPolicy(max_attempts=3)
    transport = RetryTransport(stub, policy=policy, sleep=_fail_if_called)
    # Act
    response = transport.handle_request(_request(CqsKind.NON_IDEMPOTENT_COMMAND))
    # Assert
    assert response.status_code == httpx.codes.INTERNAL_SERVER_ERROR
    assert stub.calls == 1


def test_idempotent_command_retries_5xx() -> None:
    # Arrange
    stub = _StubTransport([httpx.Response(503), httpx.Response(200)])
    transport = RetryTransport(stub, policy=RetryPolicy(max_attempts=3), sleep=lambda _: None)
    # Act
    response = transport.handle_request(_request(CqsKind.IDEMPOTENT_COMMAND))
    # Assert
    assert response.status_code == httpx.codes.OK
    assert stub.calls == 2


def test_no_retry_policy_makes_exactly_one_request() -> None:
    # Arrange
    stub = _StubTransport([httpx.Response(429)])
    transport = RetryTransport(stub, policy=NO_RETRY, sleep=_fail_if_called)
    # Act
    response = transport.handle_request(_request(CqsKind.QUERY))
    # Assert
    assert response.status_code == httpx.codes.TOO_MANY_REQUESTS
    assert stub.calls == 1


def test_close_delegates_to_next_transport() -> None:
    # Arrange
    stub = _StubTransport([])
    transport = RetryTransport(stub, policy=NO_RETRY)
    closed = []
    stub.close = lambda: closed.append(True)  # type: ignore[method-assign]
    # Act
    transport.close()
    # Assert
    assert closed == [True]
