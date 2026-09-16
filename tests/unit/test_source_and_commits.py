from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

from bitbucket.models.comment import CommentContentCreate
from bitbucket.models.comment import CommentCreate
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


@respx.mock
def test_commit_list_filters_by_include_and_exclude(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/commits").mock(
        return_value=Response(200, json={"values": [{"hash": "abc123"}], "next": None}),
    )
    # Act
    commits = list(_repository(client).commits.list(include="main", exclude="develop"))
    # Assert
    assert [commit.hash for commit in commits] == ["abc123"]
    assert dict(route.calls[0].request.url.params) == {"pagelen": "100", "include": "main", "exclude": "develop"}


@respx.mock
def test_commit_list_from_returns_commits_reachable_from_revision(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/commits/main").mock(
        return_value=Response(200, json={"values": [{"hash": "abc123"}], "next": None}),
    )
    # Act
    commits = list(_repository(client).commits.list_from("main"))
    # Assert
    assert [commit.hash for commit in commits] == ["abc123"]


@respx.mock
def test_commit_get_returns_single_commit(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/commit/abc123").mock(
        return_value=Response(200, json={"hash": "abc123", "message": "Fix bug"}),
    )
    # Act
    result = _repository(client).commits.get("abc123")
    # Assert
    assert result.message == "Fix bug"


@respx.mock
def test_commit_approve_returns_approving_account(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/commit/abc123/approve").mock(
        return_value=Response(200, json={"uuid": "{abc}"}),
    )
    # Act
    result = _repository(client).commits.approve("abc123")
    # Assert
    assert result.uuid == "{abc}"
    assert route.calls[0].request.content == b""


@respx.mock
def test_commit_unapprove_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/commit/abc123/approve").mock(
        return_value=Response(204),
    )
    # Act
    result = _repository(client).commits.unapprove("abc123")
    # Assert
    assert result is None
    assert route.called


@respx.mock
def test_commit_diff_returns_raw_text(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/diff/abc123..def456").mock(
        return_value=Response(200, text="diff --git a b"),
    )
    # Act
    result = _repository(client).commits.diff("abc123..def456")
    # Assert
    assert result == "diff --git a b"


@respx.mock
def test_commit_diffstat_returns_line_counts(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/diffstat/abc123..def456").mock(
        return_value=Response(200, json={"values": [{"lines_added": 2}], "next": None}),
    )
    # Act
    stats = list(_repository(client).commits.diffstat("abc123..def456"))
    # Assert
    assert [stat.lines_added for stat in stats] == [2]


@respx.mock
def test_commit_mbox_format_export_returns_raw_text(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/patch/abc123").mock(
        return_value=Response(200, text="From abc123"),
    )
    # Act
    result = _repository(client).commits.patch("abc123")
    # Assert
    assert result == "From abc123"


@respx.mock
def test_commit_merge_base_returns_common_ancestor_commit(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/merge-base/abc123..def456").mock(
        return_value=Response(200, json={"hash": "shared123"}),
    )
    # Act
    result = _repository(client).commits.merge_base("abc123..def456")
    # Assert
    assert result.hash == "shared123"


@respx.mock
def test_commit_comment_create_posts_content_payload(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/commit/abc123/comments").mock(
        return_value=Response(200, json={"id": 5}),
    )
    payload = CommentCreate(content=CommentContentCreate(raw="nice commit"))
    # Act
    result = _repository(client).commits.comments("abc123").create(payload)
    # Assert
    assert result.id == 5
    assert route.calls[0].request.content == b'{"content":{"raw":"nice commit"}}'


@respx.mock
def test_commit_comment_list_returns_comments(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/commit/abc123/comments").mock(
        return_value=Response(200, json={"values": [{"id": 5}], "next": None}),
    )
    # Act
    comments = list(_repository(client).commits.comments("abc123").list())
    # Assert
    assert [comment.id for comment in comments] == [5]
