from __future__ import annotations

import httpx

from bitbucket._auth import BasicAuth  # ruff: ignore[import-private-name]


def test_basic_auth_sets_authorization_header() -> None:
    # Arrange
    auth = BasicAuth("a@b.com", "tok")
    request = httpx.Request("GET", "https://api.bitbucket.org/2.0/user")
    # Act
    flow = auth.auth_flow(request)
    authorized_request = next(flow)
    # Assert
    assert authorized_request.headers["Authorization"].startswith("Basic ")
