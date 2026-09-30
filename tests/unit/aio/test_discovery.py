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
    from bitbucket.aio.client import AsyncBitbucketClient
    from bitbucket.models.pull_request import PullRequest


def _repositories(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").repositories


def _pull_requests(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").repository("repo").pull_requests


@respx.mock
async def test_repositories_list_filters_by_query_and_sort(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws").mock(
        return_value=Response(200, json={"values": [{"name": "repo"}], "next": None}),
    )
    # Act
    repositories = [item async for item in _repositories(aclient).list(q="updated_on>=2024-01-01", sort="-updated_on")]
    # Assert
    assert [repo.name for repo in repositories] == ["repo"]
    assert dict(route.calls[0].request.url.params) == {
        "pagelen": "100",
        "q": "updated_on>=2024-01-01",
        "sort": "-updated_on",
    }


@respx.mock
async def test_repositories_list_page_omits_unset_filters_from_query(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws").mock(
        return_value=Response(200, json={"values": [], "next": None}),
    )
    # Act
    await _repositories(aclient).list_page()
    # Assert
    assert dict(route.calls[0].request.url.params) == {"pagelen": "100"}


@respx.mock
async def test_repositories_list_raises_transport_error_on_connection_failure(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws").mock(side_effect=httpx.ConnectError("boom"))
    # Act
    # Assert
    with pytest.raises(TransportError, match="boom"):
        async for _ in _repositories(aclient).list():
            pass


@respx.mock
async def test_repositories_get_returns_repository(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo").mock(
        return_value=Response(200, json={"name": "repo", "full_name": "ws/repo"}),
    )
    # Act
    repository = await _repositories(aclient).get("repo")
    # Assert
    assert repository.name == "repo"
    assert repository.full_name == "ws/repo"


@respx.mock
async def test_repositories_get_returns_empty_repository_for_empty_body(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo").mock(return_value=Response(200, content=b""))
    # Act
    repository = await _repositories(aclient).get("repo")
    # Assert
    assert repository == Repository()


@respx.mock
async def test_pull_requests_by_author_sends_each_state_as_repeated_param(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/workspaces/ws/pullrequests/alice").mock(
        return_value=Response(200, json={"values": [{"id": 1}], "next": None}),
    )
    # Act
    pull_requests = [
        item async for item in aclient.workspace("ws").pull_requests_by_author("alice", states=["OPEN", "MERGED"])
    ]
    # Assert
    assert [pr.id for pr in pull_requests] == [1]
    assert route.calls[0].request.url.params.get_list("state") == ["OPEN", "MERGED"]
    assert "fields" not in route.calls[0].request.url.params


# respx matches routes in registration order, so the page-2 route (filtered on
# params) must be registered first — otherwise the unfiltered first-page route
# would also catch the page-2 request and loop forever.
@respx.mock
async def test_pull_requests_by_author_follows_next_cursor_across_pages(aclient: AsyncBitbucketClient) -> None:
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
    pull_requests = [item async for item in aclient.workspace("ws").pull_requests_by_author("alice")]
    # Assert
    assert [pr.id for pr in pull_requests] == [1, 2]


@respx.mock
async def test_pull_request_list_page_requests_the_cursor_url_verbatim(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    cursor = f"{BASE_URL}/repositories/ws/repo/pullrequests?page=2&ctx=opaque-token"
    route = respx.get(cursor).mock(return_value=Response(200, json={"values": [], "next": None}))
    # Act
    await _pull_requests(aclient).list_page(cursor=cursor)
    # Assert
    assert str(route.calls[0].request.url) == cursor


@respx.mock
async def test_pull_request_list_page_sends_no_query_params_when_unfiltered(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(
        return_value=Response(200, json={"values": [], "next": None}),
    )
    # Act
    await _pull_requests(aclient).list_page()
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
async def test_pull_request_list_page_returns_empty_page_for_payload_without_items(
    aclient: AsyncBitbucketClient,
    payload: dict[str, object],
    expected: Page[PullRequest],
) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(return_value=Response(200, json=payload))
    # Act
    page = await _pull_requests(aclient).list_page()
    # Assert
    assert page == expected


@respx.mock
async def test_pull_request_list_stops_when_payload_has_no_next_key(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(
        return_value=Response(200, json={"values": [{"id": 1}]}),
    )
    # Act
    pull_requests = [item async for item in _pull_requests(aclient).list()]
    # Assert
    assert [pr.id for pr in pull_requests] == [1]
    assert route.call_count == 1


@respx.mock
async def test_user_me_returns_the_authenticated_account(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user").mock(
        return_value=Response(200, json={"uuid": "{abc}", "display_name": "Alice"}),
    )
    # Act
    user = await aclient.user.me()
    # Assert
    assert user.uuid == "{abc}"
    assert user.display_name == "Alice"


@respx.mock
async def test_repository_default_reviewers_list_returns_reviewers(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/default-reviewers").mock(
        return_value=Response(200, json={"values": [{"uuid": "{x}", "reviewer_type": "repository"}], "next": None}),
    )
    # Act
    reviewers = [item async for item in aclient.workspace("ws").repository("repo").default_reviewers.list()]
    # Assert
    assert [reviewer.uuid for reviewer in reviewers] == ["{x}"]
    assert dict(route.calls[0].request.url.params) == {"pagelen": "100"}


@respx.mock
async def test_repository_scopes_pull_requests_to_its_slugs(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(
        return_value=Response(200, json={"values": [], "next": None}),
    )
    repository = aclient.workspace("ws").repository("repo")
    # Act
    async for _ in repository.pull_requests.list():
        pass
    # Assert
    assert route.called


@respx.mock
async def test_repository_scopes_default_reviewers_to_its_slugs(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/default-reviewers").mock(
        return_value=Response(200, json={"values": [], "next": None}),
    )
    repository = aclient.workspace("ws").repository("repo")
    # Act
    async for _ in repository.default_reviewers.list():
        pass
    # Assert
    assert route.called
