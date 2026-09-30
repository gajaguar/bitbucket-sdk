from __future__ import annotations

import warnings

import pytest

from bitbucket.config import ACCESS_TOKEN_ENV_VAR
from bitbucket.config import BasicCredentials
from bitbucket.config import BearerCredentials
from bitbucket.config import ClientConfig
from bitbucket.config import ClientOptions
from bitbucket.config import resolve_access_token
from bitbucket.config import resolve_api_token
from bitbucket.config import resolve_credentials
from bitbucket.config import resolve_email
from bitbucket.config import resolve_workspace
from bitbucket.errors import ConfigurationError
from bitbucket.errors import MissingCredentialsError


def _provider() -> str:
    return "provider-token"


def test_resolve_credentials_prefers_explicit_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "env@b.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "env-tok")
    # Act
    credentials = resolve_credentials("explicit@b.com", "explicit-tok", None)
    # Assert
    assert credentials == BasicCredentials("explicit@b.com", "explicit-tok")


def test_resolve_credentials_falls_back_to_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "env@b.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "env-tok")
    # Act
    credentials = resolve_credentials(None, None, None)
    # Assert
    assert credentials == BasicCredentials("env@b.com", "env-tok")


def test_resolve_credentials_missing_email_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.delenv("ATLASSIAN_USER_EMAIL", raising=False)
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "tok")
    # Act
    # Assert
    with pytest.raises(MissingCredentialsError, match="ATLASSIAN_USER_EMAIL"):
        resolve_credentials(None, None, None)


def test_resolve_credentials_missing_api_token_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "a@b.com")
    monkeypatch.delenv("ATLASSIAN_API_TOKEN", raising=False)
    monkeypatch.delenv("ATLASSIAN_API_KEY", raising=False)
    # Act
    # Assert
    with pytest.raises(MissingCredentialsError, match="ATLASSIAN_API_TOKEN"):
        resolve_credentials(None, None, None)


def test_resolve_credentials_without_any_source_says_where_to_create_each_credential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    for name in ("ATLASSIAN_USER_EMAIL", "ATLASSIAN_API_TOKEN", "ATLASSIAN_API_KEY", "BITBUCKET_ACCESS_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    # Act
    # Assert
    with pytest.raises(MissingCredentialsError, match=r"Security > API tokens.*Access tokens"):
        resolve_credentials(None, None, None)


def test_resolve_credentials_rejects_a_bearer_provider_with_explicit_basic() -> None:
    # Arrange
    # Act
    # Assert
    with pytest.raises(ConfigurationError, match=r"not both"):
        resolve_credentials("a@b.com", "api-token", _provider)


def test_resolve_credentials_prefers_explicit_basic_over_environment_bearer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv(ACCESS_TOKEN_ENV_VAR, "environment-bearer")
    # Act
    credentials = resolve_credentials("a@b.com", "api-token", None)
    # Assert
    assert credentials == BasicCredentials("a@b.com", "api-token")


def test_resolve_credentials_prefers_explicit_bearer_over_environment_basic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "env@b.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "env-api-token")
    # Act
    credentials = resolve_credentials(None, None, "access-token")
    # Assert
    assert credentials == BearerCredentials("access-token")


def test_resolve_credentials_ignores_incomplete_explicit_basic_with_environment_bearer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.delenv("ATLASSIAN_USER_EMAIL", raising=False)
    monkeypatch.delenv("ATLASSIAN_API_TOKEN", raising=False)
    monkeypatch.delenv("ATLASSIAN_API_KEY", raising=False)
    monkeypatch.setenv(ACCESS_TOKEN_ENV_VAR, "environment-bearer")
    # Act
    credentials = resolve_credentials("explicit@b.com", None)
    # Assert
    assert credentials == BearerCredentials("environment-bearer")


def test_resolve_credentials_rejects_both_explicit_credential_kinds() -> None:
    # Arrange
    # Act
    # Assert
    with pytest.raises(ConfigurationError, match=r"not both"):
        resolve_credentials("a@b.com", "api-token", "access-token")


def test_resolve_credentials_rejects_both_kinds_in_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "env@b.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "env-api-token")
    monkeypatch.setenv(ACCESS_TOKEN_ENV_VAR, "environment-bearer")
    # Act
    # Assert
    with pytest.raises(ConfigurationError, match=r"set only one"):
        resolve_credentials(None, None, None)


def test_resolve_credentials_does_not_warn_about_the_legacy_variable_when_bearer_wins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.delenv("ATLASSIAN_USER_EMAIL", raising=False)
    monkeypatch.delenv("ATLASSIAN_API_TOKEN", raising=False)
    monkeypatch.setenv("ATLASSIAN_API_KEY", "legacy-api-token")
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        credentials = resolve_credentials(None, None, "access-token")
    # Assert
    assert credentials == BearerCredentials("access-token")
    assert not caught


def test_resolve_credentials_accepts_bearer_without_email() -> None:
    # Arrange
    # Act
    credentials = resolve_credentials(None, None, "access-token")
    # Assert
    assert credentials == BearerCredentials("access-token")


def test_resolve_api_token_error_says_where_to_create_the_token(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.delenv("ATLASSIAN_API_TOKEN", raising=False)
    monkeypatch.delenv("ATLASSIAN_API_KEY", raising=False)
    # Act
    # Assert
    with pytest.raises(MissingCredentialsError, match="Security > API tokens"):
        resolve_api_token(None)


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


def test_resolve_access_token_falls_back_to_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv(ACCESS_TOKEN_ENV_VAR, "environment-token")
    # Act
    resolved = resolve_access_token(None)
    # Assert
    assert resolved == "environment-token"


def test_resolve_access_token_prefers_explicit_argument(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv(ACCESS_TOKEN_ENV_VAR, "environment-token")
    # Act
    resolved = resolve_access_token("explicit-token")
    # Assert
    assert resolved == "explicit-token"


def test_resolve_access_token_prefers_a_provider_over_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv(ACCESS_TOKEN_ENV_VAR, "environment-token")
    # Act
    resolved = resolve_access_token(_provider)
    # Assert
    assert resolved is _provider


def test_resolve_access_token_returns_a_provider_callable_unchanged() -> None:
    # Arrange
    # Act
    resolved = resolve_access_token(_provider)
    # Assert
    assert resolved is _provider


def test_resolve_access_token_error_names_the_environment_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.delenv(ACCESS_TOKEN_ENV_VAR, raising=False)
    # Act
    # Assert
    with pytest.raises(MissingCredentialsError, match=ACCESS_TOKEN_ENV_VAR):
        resolve_access_token(None)


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
        credentials=BasicCredentials(
            email="a@b.com",
            api_token="super-secret-token",  # ruff: ignore[hardcoded-password-func-arg]
        ),
        base_url="https://api.bitbucket.org/2.0",
    )
    # Act
    rendered = repr(config)
    # Assert
    assert "super-secret-token" not in rendered


def test_bearer_credentials_repr_never_contains_the_access_token() -> None:
    # Arrange
    config = ClientConfig(
        credentials=BearerCredentials(
            access_token="super-secret-access-token",  # ruff: ignore[hardcoded-password-func-arg]
        ),
        base_url="https://api.bitbucket.org/2.0",
    )
    # Act
    rendered = repr(config)
    # Assert
    assert "super-secret-access-token" not in rendered


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
