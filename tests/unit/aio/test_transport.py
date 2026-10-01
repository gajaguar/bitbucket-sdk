from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import respx
from httpx import Response

from bitbucket.errors import BitbucketAPIError
from bitbucket.retry import CqsKind
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.aio._transport import AsyncTransport


@respx.mock
async def test_async_request_bytes_returns_raw_response_content(atransport: AsyncTransport) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/src/abc/image.png").mock(
        return_value=Response(200, content=b"\x89PNG\r\n"),
    )
    # Act
    content = await atransport.request_bytes("GET", "/repositories/ws/repo/src/abc/image.png", kind=CqsKind.QUERY)
    # Assert
    assert content == b"\x89PNG\r\n"


@respx.mock
async def test_async_request_multipart_posts_files_and_form_data(atransport: AsyncTransport) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/src").mock(return_value=Response(204))
    # Act
    result = await atransport.request_multipart(
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
async def test_async_request_multipart_decodes_json_body(atransport: AsyncTransport) -> None:
    # Arrange
    respx.post(f"{BASE_URL}/downloads").mock(return_value=Response(200, json={"name": "file.zip"}))
    # Act
    result = await atransport.request_multipart(
        "POST",
        "/downloads",
        kind=CqsKind.NON_IDEMPOTENT_COMMAND,
        files={"file": ("file.zip", b"data", "application/zip")},
    )
    # Assert
    assert result == {"name": "file.zip"}


@respx.mock
async def test_async_request_bytes_sends_the_given_headers(atransport: AsyncTransport) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/log").mock(return_value=Response(206, content=b"abc"))
    # Act
    content = await atransport.request_bytes("GET", "/log", kind=CqsKind.QUERY, headers={"Range": "bytes=0-2"})
    # Assert
    assert content == b"abc"
    assert route.calls[0].request.headers["Range"] == "bytes=0-2"


@respx.mock
async def test_async_request_bytes_follows_a_redirect_without_leaking_authorization(
    atransport: AsyncTransport,
) -> None:
    # Arrange
    storage_url = "https://storage.example.com/log.txt"
    respx.get(f"{BASE_URL}/log").mock(return_value=Response(307, headers={"Location": storage_url}))
    storage = respx.get(storage_url).mock(return_value=Response(200, content=b"archived"))
    # Act
    content = await atransport.request_bytes("GET", "/log", kind=CqsKind.QUERY, follow_redirects=True)
    # Assert
    assert content == b"archived"
    assert "Authorization" not in storage.calls[0].request.headers


@respx.mock
async def test_async_request_bytes_does_not_follow_a_redirect_by_default(atransport: AsyncTransport) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/log").mock(
        return_value=Response(307, headers={"Location": "https://storage.example.com/log.txt"}),
    )
    # Act
    with pytest.raises(BitbucketAPIError) as raised:
        await atransport.request_bytes("GET", "/log", kind=CqsKind.QUERY)
    # Assert
    assert raised.value.status_code == 307
