from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

from bitbucket.models.comment import CommentContentCreate
from bitbucket.models.comment import CommentCreate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.aio.client import AsyncBitbucketClient


def _repository(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").repository("repo")


@respx.mock
async def test_source_list_returns_default_branch_root_entries(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/src").mock(
        return_value=Response(200, json={"values": [{"path": "README.md", "type": "commit_file"}], "next": None}),
    )
    # Act
    entries = [item async for item in _repository(aclient).source.list()]
    # Assert
    assert [entry.path for entry in entries] == ["README.md"]


@respx.mock
async def test_source_list_path_returns_entries_at_commit_and_path(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/src/abc123/src").mock(
        return_value=Response(200, json={"values": [{"path": "src/main.py"}], "next": None}),
    )
    # Act
    entries = [item async for item in _repository(aclient).source.list_path("abc123", "src")]
    # Assert
    assert [entry.path for entry in entries] == ["src/main.py"]


@respx.mock
async def test_source_read_returns_raw_file_bytes(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/src/abc123/README.md").mock(
        return_value=Response(200, content=b"# Hello"),
    )
    # Act
    content = await _repository(aclient).source.read("abc123", "README.md")
    # Assert
    assert content == b"# Hello"


@respx.mock
async def test_source_create_commit_posts_files_and_message(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/src").mock(return_value=Response(204))
    # Act
    result = await _repository(aclient).source.create_commit(
        {"README.md": b"# Hello"}, message="Update readme", branch="main"
    )
    # Assert
    assert result is None
    request_body = route.calls[0].request.content
    assert b"# Hello" in request_body
    assert b"Update readme" in request_body
    assert b"main" in request_body


@respx.mock
async def test_source_file_history_returns_commits_touching_path(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/filehistory/abc123/README.md").mock(
        return_value=Response(200, json={"values": [{"path": "README.md"}], "next": None}),
    )
    # Act
    history = [item async for item in _repository(aclient).source.file_history("abc123", "README.md")]
    # Assert
    assert [entry.path for entry in history] == ["README.md"]


@respx.mock
async def test_commit_list_filters_by_include_and_exclude(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/commits").mock(
        return_value=Response(200, json={"values": [{"hash": "abc123"}], "next": None}),
    )
    # Act
    commits = [item async for item in _repository(aclient).commits.list(include="main", exclude="develop")]
    # Assert
    assert [commit.hash for commit in commits] == ["abc123"]
    assert dict(route.calls[0].request.url.params) == {"pagelen": "100", "include": "main", "exclude": "develop"}


@respx.mock
async def test_commit_list_from_returns_commits_reachable_from_revision(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/commits/main").mock(
        return_value=Response(200, json={"values": [{"hash": "abc123"}], "next": None}),
    )
    # Act
    commits = [item async for item in _repository(aclient).commits.list_from("main")]
    # Assert
    assert [commit.hash for commit in commits] == ["abc123"]


@respx.mock
async def test_commit_get_returns_single_commit(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/commit/abc123").mock(
        return_value=Response(200, json={"hash": "abc123", "message": "Fix bug"}),
    )
    # Act
    result = await _repository(aclient).commits.get("abc123")
    # Assert
    assert result.message == "Fix bug"


@respx.mock
async def test_commit_approve_returns_approving_account(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/commit/abc123/approve").mock(
        return_value=Response(200, json={"uuid": "{abc}"}),
    )
    # Act
    result = await _repository(aclient).commits.approve("abc123")
    # Assert
    assert result.uuid == "{abc}"
    assert route.calls[0].request.content == b""


@respx.mock
async def test_commit_unapprove_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/commit/abc123/approve").mock(
        return_value=Response(204),
    )
    # Act
    result = await _repository(aclient).commits.unapprove("abc123")
    # Assert
    assert result is None
    assert route.called


@respx.mock
async def test_commit_diff_returns_raw_text(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/diff/abc123..def456").mock(
        return_value=Response(200, text="diff --git a b"),
    )
    # Act
    result = await _repository(aclient).commits.diff("abc123..def456")
    # Assert
    assert result == "diff --git a b"


@respx.mock
async def test_commit_diffstat_returns_line_counts(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/diffstat/abc123..def456").mock(
        return_value=Response(200, json={"values": [{"lines_added": 2}], "next": None}),
    )
    # Act
    stats = [item async for item in _repository(aclient).commits.diffstat("abc123..def456")]
    # Assert
    assert [stat.lines_added for stat in stats] == [2]


@respx.mock
async def test_commit_mbox_format_export_returns_raw_text(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/patch/abc123").mock(
        return_value=Response(200, text="From abc123"),
    )
    # Act
    result = await _repository(aclient).commits.patch("abc123")
    # Assert
    assert result == "From abc123"


@respx.mock
async def test_commit_merge_base_returns_common_ancestor_commit(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/merge-base/abc123..def456").mock(
        return_value=Response(200, json={"hash": "shared123"}),
    )
    # Act
    result = await _repository(aclient).commits.merge_base("abc123..def456")
    # Assert
    assert result.hash == "shared123"


@respx.mock
async def test_commit_comment_create_posts_content_payload(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/commit/abc123/comments").mock(
        return_value=Response(200, json={"id": 5}),
    )
    payload = CommentCreate(content=CommentContentCreate(raw="nice commit"))
    # Act
    result = await _repository(aclient).commits.comments("abc123").create(payload)
    # Assert
    assert result.id == 5
    assert route.calls[0].request.content == b'{"content":{"raw":"nice commit"}}'


@respx.mock
async def test_commit_comment_list_returns_comments(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/commit/abc123/comments").mock(
        return_value=Response(200, json={"values": [{"id": 5}], "next": None}),
    )
    # Act
    comments = [item async for item in _repository(aclient).commits.comments("abc123").list()]
    # Assert
    assert [comment.id for comment in comments] == [5]


@respx.mock
async def test_commits_file_conflicts_follows_next(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    first = f"{BASE_URL}/repositories/ws/repo/file-conflicts/a..b"
    respx.get(first).mock(
        return_value=Response(200, json={"values": [{"path": "a.py"}], "next": f"{first}-page-2"}),
    )
    respx.get(f"{first}-page-2").mock(return_value=Response(200, json={"values": [{"path": "b.py"}]}))
    # Act
    conflicts = [item async for item in _repository(aclient).commits.file_conflicts("a..b")]
    # Assert
    assert [conflict.path for conflict in conflicts] == ["a.py", "b.py"]


@respx.mock
async def test_commits_list_by_post_sends_form_and_posts_again_to_next(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    url = f"{BASE_URL}/repositories/ws/repo/commits"
    first = respx.post(url).mock(
        return_value=Response(200, json={"values": [{"hash": "a1"}], "next": f"{url}/page-2"}),
    )
    second = respx.post(f"{url}/page-2").mock(return_value=Response(200, json={"values": [{"hash": "b2"}]}))
    # Act
    commits = [
        item async for item in _repository(aclient).commits.list_by_post(include=["main", "dev"], exclude=["old"])
    ]
    # Assert
    assert [commit.hash for commit in commits] == ["a1", "b2"]
    for route in (first, second):
        request = route.calls[0].request
        assert request.headers["content-type"] == "application/x-www-form-urlencoded"
        assert request.content == b"include=main&include=dev&exclude=old"


@respx.mock
async def test_commits_list_from_by_post_targets_revision_and_omits_empty_filters(
    aclient: AsyncBitbucketClient,
) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/commits/main").mock(
        return_value=Response(200, json={"values": [{"hash": "a1"}]}),
    )
    # Act
    commits = [item async for item in _repository(aclient).commits.list_from_by_post("main")]
    # Assert
    assert [commit.hash for commit in commits] == ["a1"]
    assert route.calls[0].request.content == b""
