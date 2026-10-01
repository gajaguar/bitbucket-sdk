from __future__ import annotations

from logging import DEBUG

import pytest
import respx
from httpx import Response

from bitbucket._auth import auth_for  # ruff: ignore[import-private-name]
from bitbucket._transport import Transport  # ruff: ignore[import-private-name]
from bitbucket.config import BearerCredentials
from bitbucket.config import ClientConfig
from bitbucket.errors import BitbucketAPIError
from bitbucket.retry import CqsKind
from tests.conftest import BASE_URL


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
def test_request_multipart_repeats_a_field_and_sends_plain_form_fields(transport: Transport) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/snippets/ws/abc").mock(return_value=Response(200, json={}))
    parts = [("files", (None, "a.txt", None)), ("files", (None, "b.txt", None)), ("title", (None, "T", None))]
    # Act
    transport.request_multipart("PUT", "/snippets/ws/abc", kind=CqsKind.IDEMPOTENT_COMMAND, files=parts)
    # Assert
    body = route.calls[0].request.content
    assert route.calls[0].request.headers["content-type"].startswith("multipart/form-data")
    assert body.count(b'name="files"') == 2
    assert b'name="title"\r\n\r\nT' in body


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


@respx.mock
def test_request_bytes_sends_the_given_headers(transport: Transport) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/log").mock(return_value=Response(206, content=b"abc"))
    # Act
    content = transport.request_bytes("GET", "/log", kind=CqsKind.QUERY, headers={"Range": "bytes=0-2"})
    # Assert
    assert content == b"abc"
    assert route.calls[0].request.headers["Range"] == "bytes=0-2"


@respx.mock
def test_request_bytes_follows_a_redirect_without_leaking_authorization(transport: Transport) -> None:
    # Arrange
    storage_url = "https://storage.example.com/log.txt"
    respx.get(f"{BASE_URL}/log").mock(return_value=Response(307, headers={"Location": storage_url}))
    storage = respx.get(storage_url).mock(return_value=Response(200, content=b"archived"))
    # Act
    content = transport.request_bytes("GET", "/log", kind=CqsKind.QUERY, follow_redirects=True)
    # Assert
    assert content == b"archived"
    assert "Authorization" not in storage.calls[0].request.headers


@respx.mock
def test_request_bytes_does_not_follow_a_redirect_by_default(transport: Transport) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/log").mock(
        return_value=Response(307, headers={"Location": "https://storage.example.com/log.txt"}),
    )
    # Act
    with pytest.raises(BitbucketAPIError) as raised:
        transport.request_bytes("GET", "/log", kind=CqsKind.QUERY)
    # Assert
    assert raised.value.status_code == 307
