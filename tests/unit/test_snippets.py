from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import pytest
import respx
from httpx import Response

from bitbucket.errors import BitbucketAPIError
from bitbucket.errors import ForbiddenError
from bitbucket.models import Snippet
from bitbucket.models import SnippetCommentCreate
from bitbucket.models import SnippetCreate
from bitbucket.models import SnippetRole
from bitbucket.models import SnippetScm
from bitbucket.models import SnippetUpdate
from bitbucket.models.comment import CommentContentCreate
from bitbucket.models.comment import CommentParentRef
from bitbucket.models.comment import CommentUpdate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient

SNIPPETS: Final = f"{BASE_URL}/snippets/ws"
ONE: Final = f"{SNIPPETS}/abc"
SNIPPET_BODY: Final = {
    "type": "snippet",
    "id": "abc",
    "title": "Demo",
    "scm": "git",
    "is_private": True,
    "created_on": "2026-01-02T03:04:05.000000+00:00",
    "owner": {"display_name": "Ann"},
    "links": {"self": {"href": f"{ONE}"}, "html": {"href": "https://bitbucket.org/snippets/ws/abc"}},
    "files": {"a.py": {"links": {"self": {"href": f"{ONE}/files/1/a.py"}}}},
}
COMMENT_BODY: Final = {"type": "snippet_comment", "id": 7, "content": {"raw": "hi"}}


def _snippets(client: BitbucketClient):
    return client.workspace("ws").snippets


def _snippet(client: BitbucketClient):
    return client.workspace("ws").snippet("abc")


@respx.mock
def test_snippets_list_follows_the_next_link_and_filters_by_role(client: BitbucketClient) -> None:
    # Arrange
    next_url = f"{BASE_URL}/snippets-page-2/ws"
    first = respx.get(SNIPPETS, params={"role": "member"}).mock(
        return_value=Response(200, json={"values": [SNIPPET_BODY], "next": next_url})
    )
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{**SNIPPET_BODY, "id": "def"}]}))
    # Act
    result = list(_snippets(client).list(role=SnippetRole.MEMBER))
    # Assert
    assert [snippet.id for snippet in result] == ["abc", "def"]
    assert first.called


@respx.mock
def test_snippets_get_parses_the_fields_the_descriptions_show(client: BitbucketClient) -> None:
    # Arrange
    respx.get(ONE).mock(return_value=Response(200, json=SNIPPET_BODY))
    # Act
    snippet = _snippets(client).get("abc")
    # Assert
    assert snippet.scm is SnippetScm.GIT
    assert snippet.is_private is True
    assert snippet.files is not None
    assert snippet.files["a.py"].links is not None
    assert snippet.links is not None
    assert snippet.links.html is not None
    assert snippet.owner is not None
    assert snippet.owner.display_name == "Ann"


def test_snippet_id_given_as_an_integer_reads_as_text() -> None:
    # Arrange
    body = {**SNIPPET_BODY, "id": 12}
    # Act
    snippet = Snippet.model_validate(body)
    # Assert
    assert snippet.id == "12"


def test_snippet_scm_maps_an_unlisted_value_to_unknown() -> None:
    # Arrange
    body = {**SNIPPET_BODY, "scm": "hg"}
    # Act
    snippet = Snippet.model_validate(body)
    # Assert
    assert snippet.scm is SnippetScm.UNKNOWN


@respx.mock
def test_snippets_create_posts_form_fields_and_one_part_per_file(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(SNIPPETS).mock(return_value=Response(201, json=SNIPPET_BODY))
    # Act
    snippet = _snippets(client).create(
        SnippetCreate(title="Demo", is_private=True), files={"a.py": b"print(1)", "b.bin": b"\x00\x01"}
    )
    # Assert
    request = route.calls[0].request
    body = request.content
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="title"\r\n\r\nDemo' in body
    assert b'name="is_private"\r\n\r\ntrue' in body
    assert b'name="file"; filename="a.py"' in body
    assert b'name="file"; filename="b.bin"' in body
    assert snippet.id == "abc"


@respx.mock
def test_user_snippets_create_posts_to_the_unscoped_collection(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/snippets").mock(return_value=Response(201, json=SNIPPET_BODY))
    # Act
    snippet = client.snippets.create(SnippetCreate(title="Demo"), files={"a.py": b"x"})
    # Assert
    assert route.called
    assert b'filename="a.py"' in route.calls[0].request.content
    assert snippet.title == "Demo"


@respx.mock
def test_snippets_update_without_files_sends_json_metadata_and_keeps_null(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(ONE).mock(return_value=Response(200, json=SNIPPET_BODY))
    # Act
    _snippets(client).update("abc", SnippetUpdate(title=None))
    # Assert
    request = route.calls[0].request
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == {"title": None}


@respx.mock
def test_snippets_update_with_files_sends_form_data_and_names_the_deleted_files(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(ONE).mock(return_value=Response(200, json=SNIPPET_BODY))
    # Act
    _snippets(client).update(
        "abc", SnippetUpdate(title="New"), files={"a.py": b"print(2)"}, delete_files=["old.txt", "older.txt"]
    )
    # Assert
    body = route.calls[0].request.content
    assert route.calls[0].request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="title"\r\n\r\nNew' in body
    assert b'name="files"\r\n\r\nold.txt' in body
    assert b'name="files"\r\n\r\nolder.txt' in body
    assert b'name="file"; filename="a.py"' in body


@respx.mock
def test_snippets_update_with_only_deletions_still_sends_form_data(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(ONE).mock(return_value=Response(200, json=SNIPPET_BODY))
    # Act
    _snippets(client).update("abc", SnippetUpdate(), delete_files=["old.txt"])
    # Assert
    assert route.calls[0].request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="files"\r\n\r\nold.txt' in route.calls[0].request.content


@respx.mock
def test_snippets_delete_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(ONE).mock(return_value=Response(204))
    # Act
    result = _snippets(client).delete("abc")
    # Assert
    assert result is None
    assert route.called


@respx.mock
def test_snippet_comments_list_follows_the_next_link(client: BitbucketClient) -> None:
    # Arrange
    next_url = f"{BASE_URL}/snippet-comments-page-2"
    respx.get(f"{ONE}/comments").mock(return_value=Response(200, json={"values": [COMMENT_BODY], "next": next_url}))
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{**COMMENT_BODY, "id": 8}]}))
    # Act
    result = list(_snippet(client).comments.list())
    # Assert
    assert [comment.id for comment in result] == [7, 8]


@respx.mock
def test_snippet_comments_create_sends_content_and_parent(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{ONE}/comments").mock(return_value=Response(201, json=COMMENT_BODY))
    payload = SnippetCommentCreate(content=CommentContentCreate(raw="hi"), parent=CommentParentRef(id=3))
    # Act
    comment = _snippet(client).comments.create(payload)
    # Assert
    assert json.loads(route.calls[0].request.content) == {"content": {"raw": "hi"}, "parent": {"id": 3}}
    assert comment.id == 7


@respx.mock
def test_snippet_comments_get_update_and_delete_use_the_comment_path(client: BitbucketClient) -> None:
    # Arrange
    get = respx.get(f"{ONE}/comments/7").mock(return_value=Response(200, json=COMMENT_BODY))
    put = respx.put(f"{ONE}/comments/7").mock(return_value=Response(200, json=COMMENT_BODY))
    delete = respx.delete(f"{ONE}/comments/7").mock(return_value=Response(204))
    comments = _snippet(client).comments
    # Act
    comments.get(7)
    comments.update(7, CommentUpdate(content=CommentContentCreate(raw="edited")))
    result = comments.delete(7)
    # Assert
    assert json.loads(put.calls[0].request.content) == {"content": {"raw": "edited"}}
    assert get.called
    assert delete.called
    assert result is None


@respx.mock
def test_snippet_watch_and_unwatch_send_bodyless_requests(client: BitbucketClient) -> None:
    # Arrange
    put = respx.put(f"{ONE}/watch").mock(return_value=Response(204))
    delete = respx.delete(f"{ONE}/watch").mock(return_value=Response(204))
    # Act
    watched = _snippet(client).watch()
    unwatched = _snippet(client).unwatch()
    # Assert
    assert watched is None
    assert unwatched is None
    assert put.calls[0].request.content == b""
    assert delete.calls[0].request.content == b""


@respx.mock
def test_snippet_is_watching_is_true_on_204(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{ONE}/watch").mock(return_value=Response(204))
    # Act
    watching = _snippet(client).is_watching()
    # Assert
    assert watching is True


@respx.mock
def test_snippet_is_watching_is_false_on_404(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{ONE}/watch").mock(return_value=Response(404, json={"error": {"message": "no"}}))
    # Act
    watching = _snippet(client).is_watching()
    # Assert
    assert watching is False


@respx.mock
def test_snippet_is_watching_raises_on_other_errors(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{ONE}/watch").mock(return_value=Response(403, json={"error": {"message": "no"}}))
    # Act
    # Assert
    with pytest.raises(ForbiddenError):
        _snippet(client).is_watching()


@respx.mock
def test_snippet_watchers_follow_the_next_link(client: BitbucketClient) -> None:
    # Arrange
    next_url = f"{BASE_URL}/snippet-watchers-page-2"
    respx.get(f"{ONE}/watchers").mock(
        return_value=Response(200, json={"values": [{"display_name": "Ann"}], "next": next_url})
    )
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{"display_name": "Bob"}]}))
    # Act
    result = list(_snippet(client).watchers())
    # Assert
    assert [account.display_name for account in result] == ["Ann", "Bob"]


COMMIT_BODY: Final = {
    "type": "snippet_commit",
    "hash": "367ab19",
    "date": "2026-01-02T03:04:05.000000+00:00",
    "message": "Update a.py",
    "summary": {"raw": "Update a.py"},
    "author": {"raw": "Ann <ann@example.com>"},
    "parents": [{"hash": "1111111"}],
    "snippet": {"id": "abc"},
}


@respx.mock
def test_snippet_commits_follow_the_next_link(client: BitbucketClient) -> None:
    # Arrange
    next_url = f"{BASE_URL}/snippet-commits-page-2"
    respx.get(f"{ONE}/commits").mock(return_value=Response(200, json={"values": [COMMIT_BODY], "next": next_url}))
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{**COMMIT_BODY, "hash": "89abcde"}]}))
    # Act
    result = list(_snippet(client).commits())
    # Assert
    assert [commit.hash for commit in result] == ["367ab19", "89abcde"]


@respx.mock
def test_snippet_commit_parses_the_base_commit_fields(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{ONE}/commits/367ab19").mock(return_value=Response(200, json=COMMIT_BODY))
    # Act
    commit = _snippet(client).commit("367ab19")
    # Assert
    assert commit.message == "Update a.py"
    assert commit.summary is not None
    assert commit.summary.raw == "Update a.py"
    assert commit.author is not None
    assert commit.author.raw == "Ann <ann@example.com>"
    assert commit.parents is not None
    assert commit.parents[0].hash == "1111111"
    assert commit.snippet is not None
    assert commit.snippet.id == "abc"


@respx.mock
def test_snippet_file_follows_the_redirect_to_the_latest_revision(client: BitbucketClient) -> None:
    # Arrange
    target = f"{BASE_URL}/snippets/ws/abc/files/367ab19/a.py"
    respx.get(f"{ONE}/files/a.py").mock(return_value=Response(302, headers={"Location": target}))
    respx.get(target).mock(return_value=Response(200, content=b"\x00print(1)"))
    # Act
    content = _snippet(client).file("a.py")
    # Assert
    assert content == b"\x00print(1)"


@respx.mock
def test_snippet_diff_sends_the_path_filter_only_when_given(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{ONE}/367ab19/diff").mock(return_value=Response(200, text="diff --git"))
    # Act
    filtered = _snippet(client).diff("367ab19", path="a.py")
    unfiltered = _snippet(client).diff("367ab19")
    # Assert
    assert filtered == unfiltered == "diff --git"
    assert route.calls[0].request.url.params["path"] == "a.py"
    assert "path" not in route.calls[1].request.url.params


@respx.mock
def test_snippet_changes_between_versions_return_the_raw_text(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{ONE}/367ab19/patch").mock(return_value=Response(200, text="From 367ab19"))
    # Act
    patch = _snippet(client).patch("367ab19")
    # Assert
    assert patch == "From 367ab19"


@respx.mock
def test_snippet_revision_get_and_file(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{ONE}/367ab19").mock(return_value=Response(200, json=SNIPPET_BODY))
    respx.get(f"{ONE}/367ab19/files/a.py").mock(return_value=Response(200, content=b"old"))
    revision = _snippet(client).revision("367ab19")
    # Act
    snippet = revision.get()
    content = revision.file("a.py")
    # Assert
    assert snippet.id == "abc"
    assert content == b"old"


@respx.mock
def test_snippet_revision_update_and_delete_use_the_node_path(client: BitbucketClient) -> None:
    # Arrange
    put = respx.put(f"{ONE}/367ab19").mock(return_value=Response(200, json=SNIPPET_BODY))
    delete = respx.delete(f"{ONE}/367ab19").mock(return_value=Response(204))
    revision = _snippet(client).revision("367ab19")
    # Act
    revision.update(SnippetUpdate(title="New"))
    result = revision.delete()
    # Assert
    assert json.loads(put.calls[0].request.content) == {"title": "New"}
    assert result is None
    assert delete.called


@respx.mock
def test_snippet_revision_update_raises_when_it_is_not_the_latest(client: BitbucketClient) -> None:
    # Arrange
    respx.put(f"{ONE}/1111111").mock(return_value=Response(405, json={"error": {"message": "not latest"}}))
    # Act
    # Assert
    with pytest.raises(BitbucketAPIError) as raised:
        _snippet(client).revision("1111111").update(SnippetUpdate(title="New"))
    assert raised.value.status_code == 405
