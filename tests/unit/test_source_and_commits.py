from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient


def _repository(client: BitbucketClient):
    return client.workspace("ws").repository("repo")


@respx.mock
def test_source_list_returns_default_branch_root_entries(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/src").mock(
        return_value=Response(200, json={"values": [{"path": "README.md", "type": "commit_file"}], "next": None}),
    )
    # Act
    entries = list(_repository(client).source.list())
    # Assert
    assert [entry.path for entry in entries] == ["README.md"]


@respx.mock
def test_source_list_path_returns_entries_at_commit_and_path(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/src/abc123/src").mock(
        return_value=Response(200, json={"values": [{"path": "src/main.py"}], "next": None}),
    )
    # Act
    entries = list(_repository(client).source.list_path("abc123", "src"))
    # Assert
    assert [entry.path for entry in entries] == ["src/main.py"]


@respx.mock
def test_source_read_returns_raw_file_bytes(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/src/abc123/README.md").mock(
        return_value=Response(200, content=b"# Hello"),
    )
    # Act
    content = _repository(client).source.read("abc123", "README.md")
    # Assert
    assert content == b"# Hello"


@respx.mock
def test_source_create_commit_posts_files_and_message(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/src").mock(return_value=Response(204))
    # Act
    result = _repository(client).source.create_commit(
        {"README.md": b"# Hello"}, message="Update readme", branch="main"
    )
    # Assert
    assert result is None
    request_body = route.calls[0].request.content
    assert b"# Hello" in request_body
    assert b"Update readme" in request_body
    assert b"main" in request_body


@respx.mock
def test_source_file_history_returns_commits_touching_path(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/filehistory/abc123/README.md").mock(
        return_value=Response(200, json={"values": [{"path": "README.md"}], "next": None}),
    )
    # Act
    history = list(_repository(client).source.file_history("abc123", "README.md"))
    # Assert
    assert [entry.path for entry in history] == ["README.md"]
