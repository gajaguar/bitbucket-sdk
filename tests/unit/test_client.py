from __future__ import annotations

import pytest

from bitbucket.client import BitbucketClient
from bitbucket.errors import ConfigurationError
from bitbucket.errors import MissingCredentialsError


def test_context_manager_closes_transport_on_exit() -> None:
    # Arrange
    client = BitbucketClient(email="a@b.com", api_token="tok")  # ruff: ignore[hardcoded-password-func-arg]
    # Act
    with client as entered:
        assert entered is client
    # Assert
    assert client._transport._client.is_closed  # pylint: disable=protected-access


def test_missing_credentials_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.delenv("ATLASSIAN_USER_EMAIL", raising=False)
    monkeypatch.delenv("ATLASSIAN_API_KEY", raising=False)
    # Act
    # Assert
    with pytest.raises(MissingCredentialsError):
        BitbucketClient()


def test_default_workspace_uses_environment_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("BITBUCKET_WORKSPACE", "env-ws")
    client = BitbucketClient(email="a@b.com", api_token="tok")  # ruff: ignore[hardcoded-password-func-arg]
    # Act
    workspace = client.default_workspace()
    # Assert
    assert workspace.slug == "env-ws"
    client.close()


def test_default_workspace_missing_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.delenv("BITBUCKET_WORKSPACE", raising=False)
    client = BitbucketClient(email="a@b.com", api_token="tok")  # ruff: ignore[hardcoded-password-func-arg]
    # Act
    # Assert
    with pytest.raises(ConfigurationError):
        client.default_workspace()
    client.close()


def test_workspace_wraps_slug() -> None:
    # Arrange
    client = BitbucketClient(email="a@b.com", api_token="tok")  # ruff: ignore[hardcoded-password-func-arg]
    # Act
    workspace = client.workspace("my-ws")
    # Assert
    assert workspace.slug == "my-ws"
    client.close()
