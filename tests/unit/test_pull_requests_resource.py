from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

from bitbucket.models.pull_request import BranchSpec
from bitbucket.models.pull_request import EndpointSpec
from bitbucket.models.pull_request import PullRequestCreate
from bitbucket.models.pull_request import PullRequestUpdate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient


def _pull_requests(client: BitbucketClient):
    return client.workspace("ws").repository("repo").pull_requests


@respx.mock
def test_get_hits_expected_path(client: BitbucketClient) -> None:
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
def test_create_posts_serialized_payload(client: BitbucketClient) -> None:
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
def test_update_puts_serialized_payload(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/pullrequests/5").mock(
        return_value=Response(200, json={"id": 5, "title": "Renamed"}),
    )
    # Act
    result = _pull_requests(client).update(5, PullRequestUpdate(title="Renamed"))
    # Assert
    assert result.title == "Renamed"
    assert route.calls[0].request.content == b'{"title":"Renamed"}'


@respx.mock
def test_approve_posts_to_approve_endpoint(client: BitbucketClient) -> None:
    # Arrange
    respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/approve").mock(
        return_value=Response(200, json={"uuid": "{abc}"}),
    )
    # Act
    result = _pull_requests(client).approve(5)
    # Assert
    assert result.uuid == "{abc}"


@respx.mock
def test_diff_returns_raw_text(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/diff").mock(
        return_value=Response(200, text="diff --git a b"),
    )
    # Act
    diff = _pull_requests(client).diff(5)
    # Assert
    assert diff == "diff --git a b"


@respx.mock
def test_list_forwards_state_and_query_params(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(
        return_value=Response(200, json={"values": [], "next": None}),
    )
    # Act
    list(_pull_requests(client).list(state="OPEN", q='title~"fix"'))
    # Assert
    assert route.calls[0].request.url.params["state"] == "OPEN"
    assert route.calls[0].request.url.params["q"] == 'title~"fix"'


# respx matches routes in registration order, so the page-2 route (filtered on
# params) must be registered first — otherwise the unfiltered first-page route
# would also catch the page-2 request and loop forever.
@respx.mock
def test_list_page_follows_next_cursor(client: BitbucketClient) -> None:
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
    items = list(_pull_requests(client).list())
    # Assert
    assert [pr.id for pr in items] == [1, 2]


@respx.mock
def test_comments_resource_is_scoped_to_pull_request(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments").mock(
        return_value=Response(200, json={"values": [], "next": None}),
    )
    # Act
    list(_pull_requests(client).comments(5).list())
    # Assert
    assert route.called


@respx.mock
def test_statuses_resource_is_scoped_to_pull_request(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/statuses").mock(
        return_value=Response(200, json={"values": [], "next": None}),
    )
    # Act
    list(_pull_requests(client).statuses(5).list())
    # Assert
    assert route.called
