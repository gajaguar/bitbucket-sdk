from __future__ import annotations

import bitbucket


def test_version_is_exported() -> None:
    # Arrange
    # Act
    version = bitbucket.__version__
    # Assert
    assert isinstance(version, str)
    assert version


def test_credential_surface_is_public() -> None:
    # Arrange
    names = {
        "API_TOKEN_ENV_VAR",
        "EMAIL_ENV_VAR",
        "WORKSPACE_ENV_VAR",
        "ApiTokenProvider",
        "BitbucketClient",
        "ClientOptions",
        "MissingCredentialsError",
        "AuthenticationError",
        "ForbiddenError",
    }
    # Act
    missing = names - set(bitbucket.__all__)
    # Assert
    assert not missing
