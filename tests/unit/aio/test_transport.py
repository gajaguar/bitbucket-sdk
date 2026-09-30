from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

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
