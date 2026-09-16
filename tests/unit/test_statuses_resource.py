from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient


@respx.mock
def test_list_hits_statuses_endpoint(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/statuses").mock(
        return_value=Response(200, json={"values": [{"state": "SUCCESSFUL"}], "next": None}),
    )
    statuses_resource = client.workspace("ws").repository("repo").pull_requests.statuses(5)
    # Act
    statuses = list(statuses_resource.list())
    # Assert
    assert [status.state for status in statuses] == ["SUCCESSFUL"]
