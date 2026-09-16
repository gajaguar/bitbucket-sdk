from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient


@respx.mock
def test_pull_requests_by_author_hits_workspace_scoped_route(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/workspaces/ws/pullrequests/alice").mock(
        return_value=Response(200, json={"values": [{"id": 1}], "next": None}),
    )
    # Act
    prs = list(client.workspace("ws").pull_requests_by_author("alice", states=["OPEN", "MERGED"]))
    # Assert
    assert [pr.id for pr in prs] == [1]
    assert route.calls[0].request.url.params.get_list("state") == ["OPEN", "MERGED"]


@respx.mock
def test_pull_requests_by_author_follows_next_cursor(client: BitbucketClient) -> None:
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
    prs = list(client.workspace("ws").pull_requests_by_author("alice"))
    # Assert
    assert [pr.id for pr in prs] == [1, 2]


@respx.mock
def test_repository_returns_client_scoped_to_workspace(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/42").mock(
        return_value=Response(200, json={"id": 42}),
    )
    repository = client.workspace("ws").repository("repo")
    # Act
    pull_request = repository.pull_requests.get(42)
    # Assert
    assert pull_request.id == 42
    assert route.called
