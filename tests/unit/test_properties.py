from __future__ import annotations

from logging import DEBUG
from typing import TYPE_CHECKING
from typing import Any
from typing import Final

import pytest
import respx
from httpx import Response

from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient

REPO: Final = f"{BASE_URL}/repositories/ws/repo"
USER: Final = f"{BASE_URL}/users/{{u-1}}"
SCOPES: Final = {
    "repository": f"{REPO}/properties/my-app/state",
    "commit": f"{REPO}/commit/abc/properties/my-app/state",
    "user": f"{USER}/properties/my-app/state",
}
VALUE: Final = {"stage": "review", "_attributes": ["public"]}


def _properties(client: BitbucketClient, scope: str) -> Any:
    repo = client.workspace("ws").repository("repo")
    if scope == "commit":
        return repo.commits.properties("abc")
    if scope == "user":
        return client.users("{u-1}").properties
    return repo.properties


@pytest.mark.parametrize("scope", sorted(SCOPES))
@respx.mock
def test_properties_get_returns_the_stored_value(client: BitbucketClient, scope: str) -> None:
    # Arrange
    route = respx.get(SCOPES[scope]).mock(return_value=Response(200, json=VALUE))
    # Act
    value = _properties(client, scope).get("my-app", "state")
    # Assert
    assert value == VALUE
    assert route.called


@pytest.mark.parametrize("scope", sorted(SCOPES))
@respx.mock
def test_properties_put_sends_the_value_as_the_body(client: BitbucketClient, scope: str) -> None:
    # Arrange
    route = respx.put(SCOPES[scope]).mock(return_value=Response(204))
    # Act
    _properties(client, scope).put("my-app", "state", VALUE)
    # Assert
    assert route.calls[0].request.content == b'{"stage":"review","_attributes":["public"]}'


@pytest.mark.parametrize("scope", sorted(SCOPES))
@respx.mock
def test_properties_delete_returns_none(client: BitbucketClient, scope: str) -> None:
    # Arrange
    route = respx.delete(SCOPES[scope]).mock(return_value=Response(204))
    # Act
    result = _properties(client, scope).delete("my-app", "state")
    # Assert
    assert result is None
    assert route.called


@respx.mock
def test_properties_put_never_logs_the_stored_value(client: BitbucketClient, caplog: pytest.LogCaptureFixture) -> None:
    # Arrange
    respx.put(SCOPES["repository"]).mock(return_value=Response(204))
    # Act
    with caplog.at_level(DEBUG, logger="bitbucket"):
        _properties(client, "repository").put("my-app", "state", {"token": "s3cr3t-value"})
    # Assert
    assert caplog.records
    assert "s3cr3t-value" not in caplog.text
