from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import respx
from httpx import Response

from bitbucket.errors import NotFoundError
from bitbucket.errors import ServerError
from bitbucket.errors import TransportError
from bitbucket.models.comment import CommentContentCreate
from bitbucket.models.comment import CommentCreate
from bitbucket.models.comment import CommentUpdate
from bitbucket.models.pull_request import BranchSpec
from bitbucket.models.pull_request import EndpointSpec
from bitbucket.models.pull_request import PullRequestCreate
from bitbucket.models.pull_request import PullRequestUpdate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient


def _pull_requests(client: BitbucketClient):
    return client.workspace("ws").repository("repo").pull_requests


def _comments(client: BitbucketClient):
    return _pull_requests(client).comments(5)


@respx.mock
def test_pull_request_list_filters_by_state_and_query(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(
        return_value=Response(200, json={"values": [{"id": 1, "title": "Fix bug", "state": "OPEN"}], "next": None}),
    )
    # Act
    pull_requests = list(_pull_requests(client).list(state="OPEN", q='title~"fix"'))
    # Assert
    assert [pr.id for pr in pull_requests] == [1]
    assert dict(route.calls[0].request.url.params) == {"state": "OPEN", "q": 'title~"fix"'}


# respx matches routes in registration order, so the page-2 route (filtered on
# params) must be registered first — otherwise the unfiltered first-page route
# would also catch the page-2 request and loop forever.
@respx.mock
def test_pull_request_list_follows_next_cursor_across_pages(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests", params={"page": "2"}).mock(
        return_value=Response(200, json={"values": [{"id": 2}], "next": None}),
    )
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(
        return_value=Response(
            200,
            json={"values": [{"id": 1}], "next": f"{BASE_URL}/repositories/ws/repo/pullrequests?page=2"},
        ),
    )
    # Act
    pull_requests = list(_pull_requests(client).list())
    # Assert
    assert [pr.id for pr in pull_requests] == [1, 2]


@respx.mock
def test_pull_request_get_returns_pull_request(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/42").mock(
        return_value=Response(200, json={"id": 42, "title": "Fix bug"}),
    )
    # Act
    pull_request = _pull_requests(client).get(42)
    # Assert
    assert pull_request.id == 42
    assert pull_request.title == "Fix bug"


@respx.mock
def test_pull_request_get_raises_not_found_for_unknown_id(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/42").mock(
        return_value=Response(404, json={"error": {"message": "nope"}}),
    )
    # Act
    with pytest.raises(NotFoundError) as exc_info:
        _pull_requests(client).get(42)
    # Assert
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "nope"


@respx.mock
def test_pull_request_get_raises_transport_error_for_invalid_json_body(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/42").mock(
        return_value=Response(200, content=b"not json", headers={"content-type": "application/json"}),
    )
    # Act
    # Assert
    with pytest.raises(TransportError, match="Invalid JSON"):
        _pull_requests(client).get(42)


@respx.mock
def test_pull_request_diff_returns_raw_text(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/diff").mock(
        return_value=Response(200, text="diff --git a b"),
    )
    # Act
    diff = _pull_requests(client).diff(5)
    # Assert
    assert diff == "diff --git a b"


@respx.mock
def test_pull_request_diff_raises_not_found_for_unknown_id(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/diff").mock(
        return_value=Response(404, json={"error": {"message": "nope"}}),
    )
    # Act
    with pytest.raises(NotFoundError) as exc_info:
        _pull_requests(client).diff(5)
    # Assert
    assert exc_info.value.status_code == 404


@respx.mock
def test_pull_request_statuses_list_returns_build_statuses(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/statuses").mock(
        return_value=Response(200, json={"values": [{"key": "build", "state": "SUCCESSFUL"}], "next": None}),
    )
    # Act
    statuses = list(_pull_requests(client).statuses(5).list())
    # Assert
    assert [status.key for status in statuses] == ["build"]
    assert [status.state for status in statuses] == ["SUCCESSFUL"]


@respx.mock
def test_pull_request_comment_create_posts_content_payload(client: BitbucketClient) -> None:
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
def test_pull_request_comment_list_sorts_by_created_on(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments").mock(
        return_value=Response(200, json={"values": [{"id": 1}], "next": None}),
    )
    # Act
    comments = list(_comments(client).list(sort="-created_on"))
    # Assert
    assert [comment.id for comment in comments] == [1]
    assert dict(route.calls[0].request.url.params) == {"sort": "-created_on"}


@respx.mock
def test_pull_request_comment_get_returns_comment(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments/9").mock(
        return_value=Response(200, json={"id": 9}),
    )
    # Act
    comment = _comments(client).get(9)
    # Assert
    assert comment.id == 9


@respx.mock
def test_pull_request_comment_update_puts_edited_content(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments/9").mock(
        return_value=Response(200, json={"id": 9}),
    )
    # Act
    result = _comments(client).update(9, CommentUpdate(content=CommentContentCreate(raw="edited")))
    # Assert
    assert result.id == 9
    assert route.calls[0].request.content == b'{"content":{"raw":"edited"}}'


@respx.mock
def test_pull_request_comment_delete_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments/9").mock(
        return_value=Response(204),
    )
    # Act
    result = _comments(client).delete(9)
    # Assert
    assert result is None
    assert route.called


@respx.mock
def test_pull_request_approve_returns_approving_account(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/approve").mock(
        return_value=Response(200, json={"uuid": "{abc}"}),
    )
    # Act
    result = _pull_requests(client).approve(5)
    # Assert
    assert result.uuid == "{abc}"
    assert route.calls[0].request.content == b""


@respx.mock
def test_pull_request_approve_raises_server_error_on_upstream_failure(client: BitbucketClient) -> None:
    # Arrange
    respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/approve").mock(
        return_value=Response(500, text="boom"),
    )
    # Act
    with pytest.raises(ServerError) as exc_info:
        _pull_requests(client).approve(5)
    # Assert
    assert exc_info.value.status_code == 500
    assert exc_info.value.raw == "boom"


@respx.mock
def test_pull_request_create_posts_title_and_source_branch(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(
        return_value=Response(200, json={"id": 7, "title": "New PR"}),
    )
    payload = PullRequestCreate(title="New PR", source=EndpointSpec(branch=BranchSpec(name="feature")))
    # Act
    result = _pull_requests(client).create(payload)
    # Assert
    assert result.id == 7
    assert route.calls[0].request.content == b'{"title":"New PR","source":{"branch":{"name":"feature"}}}'


@respx.mock
def test_pull_request_update_puts_only_the_changed_title(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/pullrequests/5").mock(
        return_value=Response(200, json={"id": 5, "title": "Renamed"}),
    )
    # Act
    result = _pull_requests(client).update(5, PullRequestUpdate(title="Renamed"))
    # Assert
    assert result.title == "Renamed"
    assert route.calls[0].request.content == b'{"title":"Renamed"}'
