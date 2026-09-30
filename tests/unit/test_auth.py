from __future__ import annotations

import httpx
import pytest

from bitbucket._auth import BasicAuth  # ruff: ignore[import-private-name]
from bitbucket._auth import BearerAuth  # ruff: ignore[import-private-name]
from bitbucket.errors import MissingCredentialsError


def _request() -> httpx.Request:
    return httpx.Request("GET", "https://api.bitbucket.org/2.0/user")


def test_basic_auth_sets_authorization_header() -> None:
    # Arrange
    auth = BasicAuth("a@b.com", "tok")
    # Act
    flow = auth.auth_flow(_request())
    authorized_request = next(flow)
    # Assert
    assert authorized_request.headers["Authorization"].startswith("Basic ")


def test_api_token_provider_is_invoked_on_every_request() -> None:
    # Arrange
    tokens = iter(["first", "second"])
    auth = BasicAuth("a@b.com", lambda: next(tokens))
    # Act
    first = next(auth.auth_flow(_request())).headers["Authorization"]
    second = next(auth.auth_flow(_request())).headers["Authorization"]
    # Assert
    assert first != second


class _CountingProvider:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> str:
        self.calls += 1
        return "tok"


def test_api_token_provider_is_deferred_until_the_first_request() -> None:
    # Arrange
    provider = _CountingProvider()
    # Act
    auth = BasicAuth("a@b.com", provider)
    calls_before_request = provider.calls
    next(auth.auth_flow(_request()))
    # Assert
    assert calls_before_request == 0
    assert provider.calls == 1


def test_empty_api_token_provider_raises_missing_credentials_error() -> None:
    # Arrange
    auth = BasicAuth("a@b.com", lambda: "")
    # Act
    # Assert
    with pytest.raises(MissingCredentialsError, match="empty value"):
        next(auth.auth_flow(_request()))


def test_bearer_auth_sets_authorization_header() -> None:
    # Arrange
    auth = BearerAuth("access-token")
    # Act
    authorized_request = next(auth.auth_flow(_request()))
    # Assert
    assert authorized_request.headers["Authorization"] == "Bearer access-token"


def test_access_token_provider_is_invoked_on_every_request() -> None:
    # Arrange
    tokens = iter(["first", "second"])
    auth = BearerAuth(lambda: next(tokens))
    # Act
    first = next(auth.auth_flow(_request())).headers["Authorization"]
    second = next(auth.auth_flow(_request())).headers["Authorization"]
    # Assert
    assert first == "Bearer first"
    assert second == "Bearer second"


def test_access_token_provider_is_deferred_until_the_first_request() -> None:
    # Arrange
    provider = _CountingProvider()
    # Act
    auth = BearerAuth(provider)
    calls_before_request = provider.calls
    next(auth.auth_flow(_request()))
    # Assert
    assert calls_before_request == 0
    assert provider.calls == 1


def test_empty_access_token_provider_raises_missing_credentials_error() -> None:
    # Arrange
    auth = BearerAuth(lambda: "")
    # Act
    # Assert
    with pytest.raises(MissingCredentialsError, match="empty value"):
        next(auth.auth_flow(_request()))
