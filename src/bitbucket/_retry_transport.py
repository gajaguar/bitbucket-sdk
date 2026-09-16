from __future__ import annotations

from time import sleep as _default_sleep
from typing import TYPE_CHECKING

import httpx

from bitbucket.retry import CqsKind
from bitbucket.retry import RetryPolicy
from bitbucket.retry import compute_delay
from bitbucket.retry import should_retry

if TYPE_CHECKING:
    from collections.abc import Callable


def _parse_retry_after(response: httpx.Response) -> float | None:
    raw = response.headers.get("Retry-After")
    if raw is None:
        return None
    try:
        # Bitbucket only documents the delay-seconds form; an HTTP-date is ignored.
        return float(raw)
    except ValueError:
        return None


class RetryTransport(httpx.BaseTransport):
    def __init__(
        self,
        next_transport: httpx.BaseTransport,
        *,
        policy: RetryPolicy,
        sleep: Callable[[float], None] = _default_sleep,
    ) -> None:
        self.next_transport = next_transport
        self.policy = policy
        self.sleep = sleep

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        kind = request.extensions.get("bitbucket_cqs", CqsKind.NON_IDEMPOTENT_COMMAND)
        # 1-indexed: `attempt` is the count of requests already made, so that
        # `should_retry`'s `attempt >= policy.max_attempts` guard caps the total
        # request count at `max_attempts` (NO_RETRY = max_attempts=1 means exactly
        # one request, not one retry).
        attempt = 1
        while True:
            response = self.next_transport.handle_request(request)
            # Read eagerly: the body must be available to the caller whether or not we retry,
            # and leaving the connection half-consumed before a retry is a bug.
            response.read()
            if not should_retry(self.policy, kind, response.status_code, attempt):
                return response
            # compute_delay's exponent is 0-indexed by retry count (first retry -> backoff_base),
            # whereas `attempt` here is the 1-indexed count of requests already made.
            delay = compute_delay(self.policy, attempt - 1, _parse_retry_after(response))
            self.sleep(delay)
            attempt += 1

    def close(self) -> None:
        self.next_transport.close()
