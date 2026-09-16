from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import StrEnum
from random import random as _random
from typing import TYPE_CHECKING
from typing import Final

if TYPE_CHECKING:
    from collections.abc import Callable


class CqsKind(StrEnum):
    QUERY = "QUERY"
    IDEMPOTENT_COMMAND = "IDEMPOTENT_COMMAND"
    NON_IDEMPOTENT_COMMAND = "NON_IDEMPOTENT_COMMAND"


_TOO_MANY_REQUESTS: Final = 429
_SERVER_STATUSES: Final = frozenset({500, 502, 503, 504})


def _default_random_source() -> float:
    return _random()  # ruff: ignore[suspicious-non-cryptographic-random-usage]


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    backoff_base: float = 0.5
    max_backoff: float = 30.0
    retry_statuses: frozenset[int] = frozenset({429, 500, 502, 503, 504})
    respect_retry_after: bool = True
    random_source: Callable[[], float] = field(default=_default_random_source)


def should_retry(policy: RetryPolicy, kind: CqsKind, status_code: int, attempt: int) -> bool:
    if attempt >= policy.max_attempts:
        return False
    if status_code not in policy.retry_statuses:
        return False
    if status_code == _TOO_MANY_REQUESTS:
        return True
    if status_code in _SERVER_STATUSES:
        return kind is not CqsKind.NON_IDEMPOTENT_COMMAND
    return False


def compute_delay(policy: RetryPolicy, attempt: int, retry_after: float | None) -> float:
    if policy.respect_retry_after and retry_after is not None:
        return retry_after
    ceiling = min(policy.max_backoff, policy.backoff_base * (2.0**attempt))
    return policy.random_source() * ceiling


NO_RETRY: Final[RetryPolicy] = RetryPolicy(max_attempts=1)
