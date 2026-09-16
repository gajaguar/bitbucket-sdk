from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

from bitbucket.models.comment import CommentContentCreate
from bitbucket.models.comment import CommentCreate
from bitbucket.models.comment import CommentUpdate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient


def _comments(client: BitbucketClient):
    return client.workspace("ws").repository("repo").pull_requests.comments(5)


@respx.mock
def test_create_posts_to_comment_path(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments").mock(
        return_value=Response(200, json={"id": 99}),
    )
    payload = CommentCreate(content=CommentContentCreate(raw="nice"))
    # Act
    result = _comments(client).create(payload)
    # Assert
    assert result.id == 99
    assert route.calls[0].request.content == b'{"content":{"raw":"nice"}}'


@respx.mock
def test_list_paginates_with_sort(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments").mock(
        return_value=Response(200, json={"values": [{"id": 1}], "next": None}),
    )
    # Act
    comments = list(_comments(client).list(sort="-created_on"))
    # Assert
    assert [comment.id for comment in comments] == [1]
    assert route.calls[0].request.url.params["sort"] == "-created_on"


@respx.mock
def test_get_hits_expected_item_path(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments/9").mock(
        return_value=Response(200, json={"id": 9}),
    )
    # Act
    comment = _comments(client).get(9)
    # Assert
    assert comment.id == 9


@respx.mock
def test_update_puts_serialized_payload(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments/9").mock(
        return_value=Response(200, json={"id": 9}),
    )
    # Act
    _comments(client).update(9, CommentUpdate(content=CommentContentCreate(raw="edited")))
    # Assert
    assert route.calls[0].request.content == b'{"content":{"raw":"edited"}}'


@respx.mock
def test_delete_sends_delete_request(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments/9").mock(
        return_value=Response(204),
    )
    # Act
    result = _comments(client).delete(9)
    # Assert
    assert result is None
    assert route.called
