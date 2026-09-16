from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient


@respx.mock
def test_list_scopes_to_workspace(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws").mock(
        return_value=Response(200, json={"values": [{"name": "repo"}], "next": None}),
    )
    # Act
    repositories = list(client.workspace("ws").repositories.list(q="updated_on>=2024-01-01"))
    # Assert
    assert [repo.name for repo in repositories] == ["repo"]
    assert route.calls[0].request.url.params["q"] == "updated_on>=2024-01-01"


@respx.mock
def test_get_hits_repository_item_path(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo").mock(return_value=Response(200, json={"name": "repo"}))
    # Act
    repository = client.workspace("ws").repositories.get("repo")
    # Assert
    assert repository.name == "repo"
