from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from bitbucket.config import BasicCredentials
from bitbucket.config import BearerCredentials
from bitbucket.config import Credentials
from bitbucket.errors import MissingCredentialsError

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Generator


# Auth is a strategy object the Transport takes by type, so Basic and Bearer
# schemes share the same seam.
class BasicAuth(httpx.Auth):
    def __init__(self, email: str, api_token: str | Callable[[], str]) -> None:
        self._email = email
        self._api_token = api_token

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response]:
        # A callable is invoked on every request, never cached, so a rotating or
        # externally-managed token is always current.
        token = _token_for_request(self._api_token, "API token")
        return httpx.BasicAuth(self._email, token).auth_flow(request)


class BearerAuth(httpx.Auth):
    def __init__(self, access_token: str | Callable[[], str]) -> None:
        self._access_token = access_token

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response]:
        token = _token_for_request(self._access_token, "access token")
        request.headers["Authorization"] = f"Bearer {token}"
        yield request


def auth_for(credentials: Credentials) -> httpx.Auth:
    match credentials:
        case BasicCredentials(email=email, api_token=api_token):
            return BasicAuth(email, api_token)
        case BearerCredentials(access_token=access_token):
            return BearerAuth(access_token)


def _token_for_request(token: str | Callable[[], str], name: str) -> str:
    resolved = token() if callable(token) else token
    if not resolved:
        message = f"The {name} provider returned an empty value."
        raise MissingCredentialsError(message)
    return resolved
