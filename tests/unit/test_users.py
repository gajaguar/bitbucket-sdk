from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import respx
from httpx import Response

from bitbucket.models.account import AccountStatus
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient

USER_BODY: Final = {
    "type": "user",
    "account_id": "acc-1",
    "account_status": "active",
    "has_2fa_enabled": True,
    "is_staff": False,
}
EMAIL: Final = {"type": "email", "email": "a@b.com", "is_primary": True, "is_confirmed": True}


@respx.mock
def test_user_me_returns_the_user_fields(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_BODY))
    # Act
    result = client.user.me()
    # Assert
    assert result.account_status is AccountStatus.ACTIVE
    assert result.has_2fa_enabled is True
    assert result.is_staff is False


@respx.mock
def test_user_unknown_account_status_maps_to_unknown(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={**USER_BODY, "account_status": "locked"}))
    # Act
    result = client.user.me()
    # Assert
    assert result.account_status is AccountStatus.UNKNOWN


@respx.mock
def test_user_emails_follows_the_next_link(client: BitbucketClient) -> None:
    # Arrange
    next_url = f"{BASE_URL}/user/emails?page=2"
    respx.get(f"{BASE_URL}/user/emails", params={"page": "2"}).mock(
        return_value=Response(200, json={"values": [{**EMAIL, "email": "c@d.com", "is_primary": False}]})
    )
    respx.get(f"{BASE_URL}/user/emails").mock(return_value=Response(200, json={"values": [EMAIL], "next": next_url}))
    # Act
    result = list(client.user.emails())
    # Assert
    assert [(item.email, item.is_primary) for item in result] == [("a@b.com", True), ("c@d.com", False)]


@respx.mock
def test_user_email_uses_the_address_path(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/user/emails/a@b.com").mock(return_value=Response(200, json=EMAIL))
    # Act
    result = client.user.email("a@b.com")
    # Assert
    assert route.called
    assert result.is_confirmed is True


@respx.mock
def test_users_get_uses_the_selected_user_path(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/users/acc-1").mock(return_value=Response(200, json=USER_BODY))
    # Act
    result = client.users("acc-1").get()
    # Assert
    assert route.called
    assert result.account_id == "acc-1"
    assert result.account_status is AccountStatus.ACTIVE
