from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.aio.client import AsyncBitbucketClient


def _downloads(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").repository("repo").downloads


@respx.mock
async def test_download_list_returns_uploaded_files(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/downloads").mock(
        return_value=Response(200, json={"values": [{"name": "release.zip"}], "next": None}),
    )
    # Act
    downloads = [item async for item in _downloads(aclient).list()]
    # Assert
    assert [download.name for download in downloads] == ["release.zip"]


@respx.mock
async def test_download_upload_posts_file_content(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/downloads").mock(return_value=Response(201))
    # Act
    result = await _downloads(aclient).upload("release.zip", b"binary-content")
    # Assert
    assert result is None
    assert b"binary-content" in route.calls[0].request.content


@respx.mock
async def test_download_get_returns_raw_bytes(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/downloads/release.zip").mock(
        return_value=Response(200, content=b"binary-content"),
    )
    # Act
    content = await _downloads(aclient).get("release.zip")
    # Assert
    assert content == b"binary-content"


@respx.mock
async def test_download_get_follows_the_redirect_to_the_file(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    storage_url = "https://storage.example.com/release.zip"
    respx.get(f"{BASE_URL}/repositories/ws/repo/downloads/release.zip").mock(
        return_value=Response(302, headers={"Location": storage_url}),
    )
    storage = respx.get(storage_url).mock(return_value=Response(200, content=b"binary-content"))
    # Act
    content = await _downloads(aclient).get("release.zip")
    # Assert
    assert content == b"binary-content"
    assert "Authorization" not in storage.calls[0].request.headers


@respx.mock
async def test_download_delete_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/downloads/release.zip").mock(
        return_value=Response(204),
    )
    # Act
    result = await _downloads(aclient).delete("release.zip")
    # Assert
    assert result is None
    assert route.called
