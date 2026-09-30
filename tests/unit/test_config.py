from __future__ import annotations

import pytest

from bitbucket.config import ClientConfig
from bitbucket.config import ClientOptions
from bitbucket.config import resolve_api_token
from bitbucket.config import resolve_credentials
from bitbucket.config import resolve_email
from bitbucket.config import resolve_workspace
from bitbucket.errors import ConfigurationError
from bitbucket.errors import MissingCredentialsError


def test_resolve_credentials_prefers_explicit_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "env@b.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "env-tok")
    # Act
    email, token = resolve_credentials("explicit@b.com", "explicit-tok")
    # Assert
    assert email == "explicit@b.com"
    assert token == "explicit-tok"  # ruff: ignore[hardcoded-password-string]


def test_resolve_credentials_falls_back_to_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "env@b.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "env-tok")
    # Act
    email, token = resolve_credentials(None, None)
    # Assert
    assert email == "env@b.com"
    assert token == "env-tok"  # ruff: ignore[hardcoded-password-string]


def test_resolve_credentials_missing_email_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.delenv("ATLASSIAN_USER_EMAIL", raising=False)
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "tok")
    # Act
    # Assert
    with pytest.raises(MissingCredentialsError, match="ATLASSIAN_USER_EMAIL"):
        resolve_credentials(None, None)


def test_resolve_credentials_missing_api_token_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "a@b.com")
    monkeypatch.delenv("ATLASSIAN_API_TOKEN", raising=False)
    monkeypatch.delenv("ATLASSIAN_API_KEY", raising=False)
    # Act
    # Assert
    with pytest.raises(MissingCredentialsError, match="ATLASSIAN_API_TOKEN"):
        resolve_credentials(None, None)


def test_resolve_api_token_error_says_where_to_create_the_token(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.delenv("ATLASSIAN_API_TOKEN", raising=False)
    monkeypatch.delenv("ATLASSIAN_API_KEY", raising=False)
    # Act
    # Assert
    with pytest.raises(MissingCredentialsError, match="Security > API tokens"):
        resolve_api_token(None)


def _provider() -> str:
    return "provider-tok"


def test_resolve_api_token_returns_a_provider_callable_unchanged() -> None:
    # Arrange
    # Act
    resolved = resolve_api_token(_provider)
    # Assert
    assert resolved is _provider


def test_resolve_api_token_prefers_a_provider_over_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "env-tok")
    # Act
    resolved = resolve_api_token(_provider)
    # Assert
    assert resolved is _provider


def test_resolve_api_token_prefers_the_new_variable_over_the_legacy_one(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "new-tok")
    monkeypatch.setenv("ATLASSIAN_API_KEY", "legacy-tok")
    # Act
    resolved = resolve_api_token(None)
    # Assert
    assert resolved == "new-tok"


def test_resolve_api_token_accepts_the_legacy_variable_with_a_deprecation_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.delenv("ATLASSIAN_API_TOKEN", raising=False)
    monkeypatch.setenv("ATLASSIAN_API_KEY", "legacy-tok")
    # Act
    # Assert
    with pytest.warns(DeprecationWarning, match="ATLASSIAN_API_TOKEN"):
        resolved = resolve_api_token(None)
    assert resolved == "legacy-tok"


def test_resolve_email_prefers_explicit_argument(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "env@b.com")
    # Act
    email = resolve_email("explicit@b.com")
    # Assert
    assert email == "explicit@b.com"


def test_client_config_repr_never_contains_the_api_token() -> None:
    # Arrange
    config = ClientConfig(
        email="a@b.com",
        api_token="super-secret-token",  # ruff: ignore[hardcoded-password-func-arg]
        base_url="https://api.bitbucket.org/2.0",
    )
    # Act
    rendered = repr(config)
    # Assert
    assert "super-secret-token" not in rendered


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
