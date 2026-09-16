from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient


@respx.mock
def test_list_hits_default_reviewers_endpoint(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/default-reviewers").mock(
        return_value=Response(200, json={"values": [{"uuid": "{x}"}], "next": None}),
    )
    # Act
    reviewers = list(client.workspace("ws").repository("repo").default_reviewers.list())
    # Assert
    assert [reviewer.uuid for reviewer in reviewers] == ["{x}"]
