from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import pytest
import respx
from httpx import Response

from bitbucket.errors import ForbiddenError
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
    from bitbucket.aio.client import AsyncBitbucketClient

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


def _snippets(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").snippets


def _snippet(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").snippet("abc")


@respx.mock
async def test_snippets_list_follows_the_next_link_and_filters_by_role(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    next_url = f"{BASE_URL}/snippets-page-2/ws"
    first = respx.get(SNIPPETS, params={"role": "member"}).mock(
        return_value=Response(200, json={"values": [SNIPPET_BODY], "next": next_url})
    )
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{**SNIPPET_BODY, "id": "def"}]}))
    # Act
    result = [item async for item in _snippets(aclient).list(role=SnippetRole.MEMBER)]
    # Assert
    assert [snippet.id for snippet in result] == ["abc", "def"]
    assert first.called


@respx.mock
async def test_snippets_get_parses_the_fields_the_descriptions_show(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(ONE).mock(return_value=Response(200, json=SNIPPET_BODY))
    # Act
    snippet = await _snippets(aclient).get("abc")
    # Assert
    assert snippet.scm is SnippetScm.GIT
    assert snippet.is_private is True
    assert snippet.files is not None
    assert snippet.files["a.py"].links is not None
    assert snippet.links is not None
    assert snippet.links.html is not None
    assert snippet.owner is not None
    assert snippet.owner.display_name == "Ann"


@respx.mock
async def test_snippets_create_posts_form_fields_and_one_part_per_file(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(SNIPPETS).mock(return_value=Response(201, json=SNIPPET_BODY))
    # Act
    snippet = await _snippets(aclient).create(
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
async def test_user_snippets_create_posts_to_the_unscoped_collection(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/snippets").mock(return_value=Response(201, json=SNIPPET_BODY))
    # Act
    snippet = await aclient.snippets.create(SnippetCreate(title="Demo"), files={"a.py": b"x"})
    # Assert
    assert route.called
    assert b'filename="a.py"' in route.calls[0].request.content
    assert snippet.title == "Demo"


@respx.mock
async def test_snippets_update_without_files_sends_json_metadata_and_keeps_null(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(ONE).mock(return_value=Response(200, json=SNIPPET_BODY))
    # Act
    await _snippets(aclient).update("abc", SnippetUpdate(title=None))
    # Assert
    request = route.calls[0].request
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == {"title": None}


@respx.mock
async def test_snippets_update_with_files_sends_form_data_and_names_the_deleted_files(
    aclient: AsyncBitbucketClient,
) -> None:
    # Arrange
    route = respx.put(ONE).mock(return_value=Response(200, json=SNIPPET_BODY))
    # Act
    await _snippets(aclient).update(
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
async def test_snippets_update_with_only_deletions_still_sends_form_data(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(ONE).mock(return_value=Response(200, json=SNIPPET_BODY))
    # Act
    await _snippets(aclient).update("abc", SnippetUpdate(), delete_files=["old.txt"])
    # Assert
    assert route.calls[0].request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="files"\r\n\r\nold.txt' in route.calls[0].request.content


@respx.mock
async def test_snippets_delete_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(ONE).mock(return_value=Response(204))
    # Act
    result = await _snippets(aclient).delete("abc")
    # Assert
    assert result is None
    assert route.called


@respx.mock
async def test_snippet_comments_list_follows_the_next_link(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    next_url = f"{BASE_URL}/snippet-comments-page-2"
    respx.get(f"{ONE}/comments").mock(return_value=Response(200, json={"values": [COMMENT_BODY], "next": next_url}))
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{**COMMENT_BODY, "id": 8}]}))
    # Act
    result = [item async for item in _snippet(aclient).comments.list()]
    # Assert
    assert [comment.id for comment in result] == [7, 8]


@respx.mock
async def test_snippet_comments_create_sends_content_and_parent(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{ONE}/comments").mock(return_value=Response(201, json=COMMENT_BODY))
    payload = SnippetCommentCreate(content=CommentContentCreate(raw="hi"), parent=CommentParentRef(id=3))
    # Act
    comment = await _snippet(aclient).comments.create(payload)
    # Assert
    assert json.loads(route.calls[0].request.content) == {"content": {"raw": "hi"}, "parent": {"id": 3}}
    assert comment.id == 7


@respx.mock
async def test_snippet_comments_get_update_and_delete_use_the_comment_path(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    get = respx.get(f"{ONE}/comments/7").mock(return_value=Response(200, json=COMMENT_BODY))
    put = respx.put(f"{ONE}/comments/7").mock(return_value=Response(200, json=COMMENT_BODY))
    delete = respx.delete(f"{ONE}/comments/7").mock(return_value=Response(204))
    comments = _snippet(aclient).comments
    # Act
    await comments.get(7)
    await comments.update(7, CommentUpdate(content=CommentContentCreate(raw="edited")))
    result = await comments.delete(7)
    # Assert
    assert json.loads(put.calls[0].request.content) == {"content": {"raw": "edited"}}
    assert get.called
    assert delete.called
    assert result is None


@respx.mock
async def test_snippet_watch_and_unwatch_send_bodyless_requests(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    put = respx.put(f"{ONE}/watch").mock(return_value=Response(204))
    delete = respx.delete(f"{ONE}/watch").mock(return_value=Response(204))
    # Act
    watched = await _snippet(aclient).watch()
    unwatched = await _snippet(aclient).unwatch()
    # Assert
    assert watched is None
    assert unwatched is None
    assert put.calls[0].request.content == b""
    assert delete.calls[0].request.content == b""


@respx.mock
async def test_snippet_is_watching_is_true_on_204(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{ONE}/watch").mock(return_value=Response(204))
    # Act
    watching = await _snippet(aclient).is_watching()
    # Assert
    assert watching is True


@respx.mock
async def test_snippet_is_watching_is_false_on_404(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{ONE}/watch").mock(return_value=Response(404, json={"error": {"message": "no"}}))
    # Act
    watching = await _snippet(aclient).is_watching()
    # Assert
    assert watching is False


@respx.mock
async def test_snippet_is_watching_raises_on_other_errors(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{ONE}/watch").mock(return_value=Response(403, json={"error": {"message": "no"}}))
    # Act
    # Assert
    with pytest.raises(ForbiddenError):
        await _snippet(aclient).is_watching()


@respx.mock
async def test_snippet_watchers_follow_the_next_link(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    next_url = f"{BASE_URL}/snippet-watchers-page-2"
    respx.get(f"{ONE}/watchers").mock(
        return_value=Response(200, json={"values": [{"display_name": "Ann"}], "next": next_url})
    )
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{"display_name": "Bob"}]}))
    # Act
    result = [item async for item in _snippet(aclient).watchers()]
    # Assert
    assert [account.display_name for account in result] == ["Ann", "Bob"]
