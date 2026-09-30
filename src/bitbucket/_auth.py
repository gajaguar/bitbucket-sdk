from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from bitbucket.errors import MissingCredentialsError

if TYPE_CHECKING:
    from collections.abc import Generator

    from bitbucket.config import ApiTokenProvider


class BasicAuth(httpx.Auth):
    # Auth is a strategy object the Transport takes by type, not a hardcoded call; a
    # future OAuth bearer scheme arrives through the same seam.
    def __init__(self, email: str, api_token: str | ApiTokenProvider) -> None:
        self._email = email
        self._api_token = api_token

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response]:
        # A callable is invoked on every request, never cached, so a rotating or
        # externally-managed token is always current.
        token = self._api_token() if callable(self._api_token) else self._api_token
        if not token:
            message = "The API token provider returned an empty value."
            raise MissingCredentialsError(message)
        return httpx.BasicAuth(self._email, token).auth_flow(request)
