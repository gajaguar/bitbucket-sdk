from __future__ import annotations

from base64 import b64encode

import pytest
import respx
from httpx import Response

from bitbucket.client import BitbucketClient
from bitbucket.config import ClientOptions
from bitbucket.errors import ConfigurationError
from bitbucket.errors import MissingCredentialsError
from bitbucket.retry import NO_RETRY
from tests.conftest import BASE_URL


def _basic_auth_header(email: str, api_token: str) -> str:
    return "Basic " + b64encode(f"{email}:{api_token}".encode()).decode()


@respx.mock
def test_client_prefers_explicit_credentials_over_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "env@b.com")
    monkeypatch.setenv("ATLASSIAN_API_KEY", "env-tok")
    route = respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={}))
    # Act
    with BitbucketClient(
        email="explicit@b.com",
        api_token="explicit-tok",  # ruff: ignore[hardcoded-password-func-arg]
        options=ClientOptions(retry=NO_RETRY),
    ) as client:
        client.user.me()
    # Assert
    assert route.calls[0].request.headers["Authorization"] == _basic_auth_header("explicit@b.com", "explicit-tok")


@respx.mock
def test_client_falls_back_to_environment_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "env@b.com")
    monkeypatch.setenv("ATLASSIAN_API_KEY", "env-tok")
    route = respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={}))
    # Act
    with BitbucketClient(options=ClientOptions(retry=NO_RETRY)) as client:
        client.user.me()
    # Assert
    assert route.calls[0].request.headers["Authorization"] == _basic_auth_header("env@b.com", "env-tok")


def test_client_without_credentials_raises_missing_credentials_error(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.delenv("ATLASSIAN_USER_EMAIL", raising=False)
    monkeypatch.delenv("ATLASSIAN_API_KEY", raising=False)
    # Act
    # Assert
    with pytest.raises(MissingCredentialsError, match="ATLASSIAN_USER_EMAIL"):
        BitbucketClient()


@respx.mock
def test_client_sends_the_default_user_agent(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={}))
    # Act
    client.user.me()
    # Assert
    assert route.calls[0].request.headers["User-Agent"] == "bitbucket-unofficial-sdk/0.2"


@respx.mock
def test_client_uses_the_base_url_option_for_every_request() -> None:
    # Arrange
    custom_base_url = "https://bitbucket.example.com/2.0"
    route = respx.get(f"{custom_base_url}/user").mock(return_value=Response(200, json={"uuid": "{abc}"}))
    # Act
    with BitbucketClient(
        email="a@b.com",
        api_token="tok",  # ruff: ignore[hardcoded-password-func-arg]
        options=ClientOptions(base_url=custom_base_url, retry=NO_RETRY),
    ) as client:
        user = client.user.me()
    # Assert
    assert user.uuid == "{abc}"
    assert route.called


def test_default_workspace_reads_the_workspace_environment_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("BITBUCKET_WORKSPACE", "env-ws")
    client = BitbucketClient(
        email="a@b.com",
        api_token="tok",  # ruff: ignore[hardcoded-password-func-arg]
        options=ClientOptions(retry=NO_RETRY),
    )
    # Act
    workspace = client.default_workspace()
    # Assert
    assert workspace.slug == "env-ws"
    client.close()


def test_default_workspace_without_environment_variable_raises_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.delenv("BITBUCKET_WORKSPACE", raising=False)
    client = BitbucketClient(
        email="a@b.com",
        api_token="tok",  # ruff: ignore[hardcoded-password-func-arg]
        options=ClientOptions(retry=NO_RETRY),
    )
    # Act
    # Assert
    with pytest.raises(ConfigurationError, match="BITBUCKET_WORKSPACE"):
        client.default_workspace()
    client.close()


def test_workspace_returns_a_client_for_the_given_slug(client: BitbucketClient) -> None:
    # Arrange
    slug = "my-ws"
    # Act
    workspace = client.workspace(slug)
    # Assert
    assert workspace.slug == slug


def test_context_manager_yields_the_client_itself() -> None:
    # Arrange
    client = BitbucketClient(
        email="a@b.com",
        api_token="tok",  # ruff: ignore[hardcoded-password-func-arg]
        options=ClientOptions(retry=NO_RETRY),
    )
    # Act
    with client as entered:
        # Assert
        assert entered is client
    client.close()


@respx.mock
def test_context_manager_exit_stops_requests_from_being_sent() -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={}))
    with BitbucketClient(
        email="a@b.com",
        api_token="tok",  # ruff: ignore[hardcoded-password-func-arg]
        options=ClientOptions(retry=NO_RETRY),
    ) as entered:
        pass
    # Act
    # Assert
    with pytest.raises(RuntimeError, match="has been closed"):
        entered.user.me()
    assert not route.called
