from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient


def _downloads(client: BitbucketClient):
    return client.workspace("ws").repository("repo").downloads


@respx.mock
def test_download_list_returns_uploaded_files(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/downloads").mock(
        return_value=Response(200, json={"values": [{"name": "release.zip"}], "next": None}),
    )
    # Act
    downloads = list(_downloads(client).list())
    # Assert
    assert [download.name for download in downloads] == ["release.zip"]


@respx.mock
def test_download_upload_posts_file_content(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/downloads").mock(return_value=Response(201))
    # Act
    result = _downloads(client).upload("release.zip", b"binary-content")
    # Assert
    assert result is None
    assert b"binary-content" in route.calls[0].request.content


@respx.mock
def test_download_get_returns_raw_bytes(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/downloads/release.zip").mock(
        return_value=Response(200, content=b"binary-content"),
    )
    # Act
    content = _downloads(client).get("release.zip")
    # Assert
    assert content == b"binary-content"


@respx.mock
def test_download_delete_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/downloads/release.zip").mock(
        return_value=Response(204),
    )
    # Act
    result = _downloads(client).delete("release.zip")
    # Assert
    assert result is None
    assert route.called
