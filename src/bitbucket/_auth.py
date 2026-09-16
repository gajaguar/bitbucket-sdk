from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from collections.abc import Generator


class BasicAuth(httpx.Auth):
    # Thin wrapper around httpx.BasicAuth so auth is a strategy object the
    # Transport takes by type, not a hardcoded call — the seam a future
    # OAuth bearer scheme (X-Addon-Token) arrives through.
    def __init__(self, email: str, api_token: str) -> None:
        self._delegate = httpx.BasicAuth(email, api_token)

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response]:
        return self._delegate.auth_flow(request)
