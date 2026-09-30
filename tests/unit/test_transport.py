from __future__ import annotations

from logging import DEBUG
from typing import TYPE_CHECKING

import respx
from httpx import Response

from bitbucket._auth import auth_for  # ruff: ignore[import-private-name]
from bitbucket._transport import Transport  # ruff: ignore[import-private-name]
from bitbucket.config import BearerCredentials
from bitbucket.config import ClientConfig
from bitbucket.retry import CqsKind
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    import pytest


@respx.mock
def test_request_bytes_returns_raw_response_content(transport: Transport) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/src/abc/image.png").mock(
        return_value=Response(200, content=b"\x89PNG\r\n"),
    )
    # Act
    content = transport.request_bytes("GET", "/repositories/ws/repo/src/abc/image.png", kind=CqsKind.QUERY)
    # Assert
    assert content == b"\x89PNG\r\n"


@respx.mock
def test_request_multipart_posts_files_and_form_data(transport: Transport) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/src").mock(return_value=Response(204))
    # Act
    result = transport.request_multipart(
        "POST",
        "/repositories/ws/repo/src",
        kind=CqsKind.NON_IDEMPOTENT_COMMAND,
        files={"README.md": ("README.md", b"hello", "text/markdown")},
        data={"message": "Add readme"},
    )
    # Assert
    assert result is None
    request_body = route.calls[0].request.content
    assert b"hello" in request_body
    assert b"Add readme" in request_body


@respx.mock
def test_request_multipart_decodes_json_body(transport: Transport) -> None:
    # Arrange
    respx.post(f"{BASE_URL}/downloads").mock(return_value=Response(200, json={"name": "file.zip"}))
    # Act
    result = transport.request_multipart(
        "POST",
        "/downloads",
        kind=CqsKind.NON_IDEMPOTENT_COMMAND,
        files={"file": ("file.zip", b"data", "application/zip")},
    )
    # Assert
    assert result == {"name": "file.zip"}


@respx.mock
def test_debug_log_never_contains_the_api_token(transport: Transport, caplog: pytest.LogCaptureFixture) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={}))
    # Act
    with caplog.at_level(DEBUG, logger="bitbucket"):
        transport.request("GET", "/user", kind=CqsKind.QUERY)
    # Assert
    assert caplog.records
    assert "tok" not in caplog.text
    assert "a@b.com" not in caplog.text


@respx.mock
def test_debug_log_never_contains_the_bearer_token(caplog: pytest.LogCaptureFixture) -> None:
    # Arrange
    secret = "bearer-secret"  # ruff: ignore[hardcoded-password-string]
    config = ClientConfig(
        credentials=BearerCredentials(access_token=secret),
        base_url=BASE_URL,
    )
    transport = Transport(config, auth_for(config.credentials))
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={}))
    # Act
    try:
        with caplog.at_level(DEBUG, logger="bitbucket"):
            transport.request("GET", "/user", kind=CqsKind.QUERY)
    finally:
        transport.close()
    # Assert
    assert caplog.records
    assert secret not in caplog.text
