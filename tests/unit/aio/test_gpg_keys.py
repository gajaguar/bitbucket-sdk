from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import respx
from httpx import Response

from bitbucket.models.gpg_key import GpgKeyCreate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.aio.client import AsyncBitbucketClient

KEYS: Final = f"{BASE_URL}/users/acc-1/gpg-keys"
SUBKEY: Final = {"type": "gpg_account_key", "fingerprint": "BBBB", "parent_fingerprint": "AAAA"}
KEY_BODY: Final = {
    "type": "gpg_account_key",
    "fingerprint": "AAAA",
    "key_id": "1234",
    "name": "Signing",
    "added_on": "2026-01-02T03:04:05.000000+00:00",
    "subkeys": [SUBKEY],
}


@respx.mock
async def test_gpg_keys_list_follows_the_next_link(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(KEYS, params={"page": "2"}).mock(
        return_value=Response(200, json={"values": [{**KEY_BODY, "fingerprint": "CCCC"}]})
    )
    respx.get(KEYS).mock(return_value=Response(200, json={"values": [KEY_BODY], "next": f"{KEYS}?page=2"}))
    # Act
    result = [item async for item in aclient.users("acc-1").gpg_keys.list()]
    # Assert
    assert [key.fingerprint for key in result] == ["AAAA", "CCCC"]


@respx.mock
async def test_gpg_keys_get_parses_the_subkeys(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{KEYS}/AAAA").mock(return_value=Response(200, json=KEY_BODY))
    # Act
    result = await aclient.users("acc-1").gpg_keys.get("AAAA")
    # Assert
    assert route.called
    assert result.subkeys is not None
    assert result.subkeys[0].parent_fingerprint == "AAAA"
    assert result.added_on is not None


@respx.mock
async def test_gpg_keys_create_posts_the_key(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(KEYS).mock(return_value=Response(201, json=KEY_BODY))
    # Act
    result = await aclient.users("acc-1").gpg_keys.create(GpgKeyCreate(key="-----BEGIN PGP", name="Signing"))
    # Assert
    assert json.loads(route.calls.last.request.content) == {"key": "-----BEGIN PGP", "name": "Signing"}
    assert result.name == "Signing"


@respx.mock
async def test_gpg_keys_delete_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{KEYS}/AAAA").mock(return_value=Response(204))
    # Act
    result = await aclient.users("acc-1").gpg_keys.delete("AAAA")
    # Assert
    assert route.called
    assert result is None
