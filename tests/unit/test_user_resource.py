from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient


@respx.mock
def test_me_hits_user_endpoint(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={"uuid": "{abc}"}))
    # Act
    user = client.user.me()
    # Assert
    assert user.uuid == "{abc}"
