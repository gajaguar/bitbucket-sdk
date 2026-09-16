from __future__ import annotations

import pytest

from bitbucket.config import ClientOptions
from bitbucket.config import resolve_credentials
from bitbucket.config import resolve_workspace
from bitbucket.errors import ConfigurationError
from bitbucket.errors import MissingCredentialsError


def test_resolve_credentials_prefers_explicit_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "env@b.com")
    monkeypatch.setenv("ATLASSIAN_API_KEY", "env-tok")
    # Act
    email, token = resolve_credentials("explicit@b.com", "explicit-tok")
    # Assert
    assert email == "explicit@b.com"
    assert token == "explicit-tok"  # ruff: ignore[hardcoded-password-string]


def test_resolve_credentials_falls_back_to_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "env@b.com")
    monkeypatch.setenv("ATLASSIAN_API_KEY", "env-tok")
    # Act
    email, token = resolve_credentials(None, None)
    # Assert
    assert email == "env@b.com"
    assert token == "env-tok"  # ruff: ignore[hardcoded-password-string]


def test_resolve_credentials_missing_email_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.delenv("ATLASSIAN_USER_EMAIL", raising=False)
    monkeypatch.setenv("ATLASSIAN_API_KEY", "tok")
    # Act
    # Assert
    with pytest.raises(MissingCredentialsError, match="ATLASSIAN_USER_EMAIL"):
        resolve_credentials(None, None)


def test_resolve_credentials_missing_api_token_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "a@b.com")
    monkeypatch.delenv("ATLASSIAN_API_KEY", raising=False)
    # Act
    # Assert
    with pytest.raises(MissingCredentialsError, match="ATLASSIAN_API_KEY"):
        resolve_credentials(None, None)


def test_resolve_workspace_prefers_explicit_argument(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("BITBUCKET_WORKSPACE", "env-ws")
    # Act
    workspace = resolve_workspace("explicit-ws")
    # Assert
    assert workspace == "explicit-ws"


def test_resolve_workspace_falls_back_to_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("BITBUCKET_WORKSPACE", "env-ws")
    # Act
    workspace = resolve_workspace(None)
    # Assert
    assert workspace == "env-ws"


def test_resolve_workspace_missing_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.delenv("BITBUCKET_WORKSPACE", raising=False)
    # Act
    # Assert
    with pytest.raises(ConfigurationError, match="BITBUCKET_WORKSPACE"):
        resolve_workspace(None)


def test_client_options_defaults() -> None:
    # Arrange
    # Act
    options = ClientOptions()
    # Assert
    assert options.base_url is None
    assert options.timeout == pytest.approx(30.0)
    assert options.retry is None
    assert options.event_hooks is None
