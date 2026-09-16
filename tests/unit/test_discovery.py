from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest
import respx
from httpx import Response

from bitbucket._pagination import Page  # ruff: ignore[import-private-name]
from bitbucket.errors import TransportError
from bitbucket.models.repository import Repository
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient
    from bitbucket.models.pull_request import PullRequest


def _repositories(client: BitbucketClient):
    return client.workspace("ws").repositories


def _pull_requests(client: BitbucketClient):
    return client.workspace("ws").repository("repo").pull_requests


@respx.mock
def test_repositories_list_filters_by_query_and_sort(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws").mock(
        return_value=Response(200, json={"values": [{"name": "repo"}], "next": None}),
    )
    # Act
    repositories = list(_repositories(client).list(q="updated_on>=2024-01-01", sort="-updated_on"))
    # Assert
    assert [repo.name for repo in repositories] == ["repo"]
    assert dict(route.calls[0].request.url.params) == {
        "pagelen": "100",
        "q": "updated_on>=2024-01-01",
        "sort": "-updated_on",
    }


@respx.mock
def test_repositories_list_page_omits_unset_filters_from_query(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws").mock(
        return_value=Response(200, json={"values": [], "next": None}),
    )
    # Act
    _repositories(client).list_page()
    # Assert
    assert dict(route.calls[0].request.url.params) == {"pagelen": "100"}


@respx.mock
def test_repositories_list_raises_transport_error_on_connection_failure(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws").mock(side_effect=httpx.ConnectError("boom"))
    # Act
    # Assert
    with pytest.raises(TransportError, match="boom"):
        list(_repositories(client).list())


@respx.mock
def test_repositories_get_returns_repository(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo").mock(
        return_value=Response(200, json={"name": "repo", "full_name": "ws/repo"}),
    )
    # Act
    repository = _repositories(client).get("repo")
    # Assert
    assert repository.name == "repo"
    assert repository.full_name == "ws/repo"


@respx.mock
def test_repositories_get_returns_empty_repository_for_empty_body(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo").mock(return_value=Response(200, content=b""))
    # Act
    repository = _repositories(client).get("repo")
    # Assert
    assert repository == Repository()


@respx.mock
def test_pull_requests_by_author_sends_each_state_as_repeated_param(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/workspaces/ws/pullrequests/alice").mock(
        return_value=Response(200, json={"values": [{"id": 1}], "next": None}),
    )
    # Act
    pull_requests = list(client.workspace("ws").pull_requests_by_author("alice", states=["OPEN", "MERGED"]))
    # Assert
    assert [pr.id for pr in pull_requests] == [1]
    assert route.calls[0].request.url.params.get_list("state") == ["OPEN", "MERGED"]
    assert "fields" not in route.calls[0].request.url.params


# respx matches routes in registration order, so the page-2 route (filtered on
# params) must be registered first — otherwise the unfiltered first-page route
# would also catch the page-2 request and loop forever.
@respx.mock
def test_pull_requests_by_author_follows_next_cursor_across_pages(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/workspaces/ws/pullrequests/alice", params={"page": "2"}).mock(
        return_value=Response(200, json={"values": [{"id": 2}], "next": None}),
    )
    respx.get(f"{BASE_URL}/workspaces/ws/pullrequests/alice").mock(
        return_value=Response(
            200,
            json={"values": [{"id": 1}], "next": f"{BASE_URL}/workspaces/ws/pullrequests/alice?page=2"},
        ),
    )
    # Act
    pull_requests = list(client.workspace("ws").pull_requests_by_author("alice"))
    # Assert
    assert [pr.id for pr in pull_requests] == [1, 2]


@respx.mock
def test_pull_request_list_page_requests_the_cursor_url_verbatim(client: BitbucketClient) -> None:
    # Arrange
    cursor = f"{BASE_URL}/repositories/ws/repo/pullrequests?page=2&ctx=opaque-token"
    route = respx.get(cursor).mock(return_value=Response(200, json={"values": [], "next": None}))
    # Act
    _pull_requests(client).list_page(cursor=cursor)
    # Assert
    assert str(route.calls[0].request.url) == cursor


@respx.mock
def test_pull_request_list_page_sends_no_query_params_when_unfiltered(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(
        return_value=Response(200, json={"values": [], "next": None}),
    )
    # Act
    _pull_requests(client).list_page()
    # Assert
    assert str(route.calls[0].request.url) == f"{BASE_URL}/repositories/ws/repo/pullrequests"


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"next": None}, Page(items=[], next_cursor=None, size=None)),
        ({"values": None, "size": 0}, Page(items=[], next_cursor=None, size=0)),
        (
            {"values": [], "next": f"{BASE_URL}/repositories/ws/repo/pullrequests?page=2", "size": 0},
            Page(items=[], next_cursor=f"{BASE_URL}/repositories/ws/repo/pullrequests?page=2", size=0),
        ),
    ],
    ids=["values-missing", "values-null", "values-empty"],
)
@respx.mock
def test_pull_request_list_page_returns_empty_page_for_payload_without_items(
    client: BitbucketClient,
    payload: dict[str, object],
    expected: Page[PullRequest],
) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(return_value=Response(200, json=payload))
    # Act
    page = _pull_requests(client).list_page()
    # Assert
    assert page == expected


@respx.mock
def test_pull_request_list_stops_when_payload_has_no_next_key(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(
        return_value=Response(200, json={"values": [{"id": 1}]}),
    )
    # Act
    pull_requests = list(_pull_requests(client).list())
    # Assert
    assert [pr.id for pr in pull_requests] == [1]
    assert route.call_count == 1


@respx.mock
def test_user_me_returns_the_authenticated_account(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user").mock(
        return_value=Response(200, json={"uuid": "{abc}", "display_name": "Alice"}),
    )
    # Act
    user = client.user.me()
    # Assert
    assert user.uuid == "{abc}"
    assert user.display_name == "Alice"


@respx.mock
def test_repository_default_reviewers_list_returns_reviewers(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/default-reviewers").mock(
        return_value=Response(200, json={"values": [{"uuid": "{x}", "reviewer_type": "repository"}], "next": None}),
    )
    # Act
    reviewers = list(client.workspace("ws").repository("repo").default_reviewers.list())
    # Assert
    assert [reviewer.uuid for reviewer in reviewers] == ["{x}"]
    assert dict(route.calls[0].request.url.params) == {"pagelen": "100"}


@respx.mock
def test_repository_scopes_pull_requests_to_its_slugs(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(
        return_value=Response(200, json={"values": [], "next": None}),
    )
    repository = client.workspace("ws").repository("repo")
    # Act
    list(repository.pull_requests.list())
    # Assert
    assert route.called


@respx.mock
def test_repository_scopes_default_reviewers_to_its_slugs(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/default-reviewers").mock(
        return_value=Response(200, json={"values": [], "next": None}),
    )
    repository = client.workspace("ws").repository("repo")
    # Act
    list(repository.default_reviewers.list())
    # Assert
    assert route.called
