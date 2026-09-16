from __future__ import annotations

from typing import Final

import bitbucket

EXPECTED_EXPORTS: Final = (  # ruff: ignore[split-static-string]
    "NO_RETRY AccountId AuthenticationError BitbucketAPIError BitbucketError CommentId CommitHash "
    "ConfigurationError ConflictError CqsKind ErrorBody ForbiddenError MissingCredentialsError NotFoundError "
    "PullRequestId RateLimitError RepositorySlug RetryPolicy ServerError TransportError Uuid ValidationError "
    "WorkspaceSlug __version__"
).split()


def test_version_is_exported() -> None:
    # Arrange
    # Act
    version = bitbucket.__version__
    # Assert
    assert version == "0.0.0"


def test_public_import_surface() -> None:
    # Arrange
    # Act
    exported = bitbucket.__all__
    # Assert
    assert exported == EXPECTED_EXPORTS
    assert all(hasattr(bitbucket, name) for name in exported)
