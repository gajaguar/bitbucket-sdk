from __future__ import annotations

import bitbucket


def test_async_client_is_exported() -> None:
    # Arrange
    # Act
    # Assert
    assert "AsyncBitbucketClient" in bitbucket.__all__


def test_credential_surface_is_public() -> None:
    # Arrange
    names = {
        "ACCESS_TOKEN_ENV_VAR",
        "API_TOKEN_ENV_VAR",
        "EMAIL_ENV_VAR",
        "WORKSPACE_ENV_VAR",
        "AccessTokenProvider",
        "ApiTokenProvider",
        "AsyncBitbucketClient",
        "ClientOptions",
        "MissingCredentialsError",
        "AuthenticationError",
        "ForbiddenError",
    }
    # Act
    missing = names - set(bitbucket.__all__)
    # Assert
    assert not missing
