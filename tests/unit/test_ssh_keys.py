from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import respx
from httpx import Response

from bitbucket.models.ssh_key import SshKeyCreate
from bitbucket.models.ssh_key import SshKeyUpdate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient

KEYS: Final = f"{BASE_URL}/users/acc-1/ssh-keys"
KEY_BODY: Final = {
    "type": "ssh_key",
    "uuid": "{k-1}",
    "key": "ssh-ed25519 AAAA",
    "label": "Work",
    "fingerprint": "SHA256:abc",
    "created_on": "2026-01-02T03:04:05.000000+00:00",
    "owner": {"type": "user", "account_id": "acc-1"},
}


@respx.mock
def test_ssh_keys_list_follows_the_next_link(client: BitbucketClient) -> None:
    # Arrange
    respx.get(KEYS, params={"page": "2"}).mock(
        return_value=Response(200, json={"values": [{**KEY_BODY, "uuid": "{k-2}"}]})
    )
    respx.get(KEYS).mock(return_value=Response(200, json={"values": [KEY_BODY], "next": f"{KEYS}?page=2"}))
    # Act
    result = list(client.users("acc-1").ssh_keys.list())
    # Assert
    assert [key.uuid for key in result] == ["{k-1}", "{k-2}"]


@respx.mock
def test_ssh_keys_get_uses_the_key_id_path(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{KEYS}/{{k-1}}").mock(return_value=Response(200, json=KEY_BODY))
    # Act
    result = client.users("acc-1").ssh_keys.get("{k-1}")
    # Assert
    assert route.called
    assert result.fingerprint == "SHA256:abc"
    assert result.created_on is not None


@respx.mock
def test_ssh_keys_create_posts_the_key_and_the_expiry(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(KEYS, params={"expires_on": "2027-01-01"}).mock(return_value=Response(201, json=KEY_BODY))
    # Act
    result = client.users("acc-1").ssh_keys.create(
        SshKeyCreate(key="ssh-ed25519 AAAA", label="Work"), expires_on="2027-01-01"
    )
    # Assert
    assert json.loads(route.calls.last.request.content) == {"key": "ssh-ed25519 AAAA", "label": "Work"}
    assert result.label == "Work"


@respx.mock
def test_ssh_keys_create_omits_the_expiry_when_absent(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(KEYS).mock(return_value=Response(201, json=KEY_BODY))
    # Act
    client.users("acc-1").ssh_keys.create(SshKeyCreate(key="ssh-ed25519 AAAA"))
    # Assert
    assert route.calls.last.request.url.query == b""
    assert json.loads(route.calls.last.request.content) == {"key": "ssh-ed25519 AAAA"}


@respx.mock
def test_ssh_keys_update_puts_the_label(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{KEYS}/{{k-1}}").mock(return_value=Response(200, json={**KEY_BODY, "label": "Home"}))
    # Act
    result = client.users("acc-1").ssh_keys.update("{k-1}", SshKeyUpdate(label="Home"))
    # Assert
    assert json.loads(route.calls.last.request.content) == {"label": "Home"}
    assert result.label == "Home"


@respx.mock
def test_ssh_keys_delete_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{KEYS}/{{k-1}}").mock(return_value=Response(204))
    # Act
    result = client.users("acc-1").ssh_keys.delete("{k-1}")
    # Assert
    assert route.called
    assert result is None
