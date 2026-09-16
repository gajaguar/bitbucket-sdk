from __future__ import annotations

from typing import Final

import bitbucket

EXPECTED_EXPORTS: Final = (  # ruff: ignore[split-static-string]
    "NO_RETRY Account AccountId AccountLinks AuthenticationError AuthorRef BitbucketAPIError BitbucketError "
    "Branch BranchSpec ClientOptions Comment CommentContentCreate CommentCreate CommentId CommentInline "
    "CommentInlineCreate CommentParentRef CommentResolution CommentUpdate Commit CommitHash CommitRef "
    "ConfigurationError ConflictError CqsKind DefaultReviewer EndpointSpec ErrorBody ForbiddenError "
    "ForkPolicy Link Links Markup MergeStrategy MissingCredentialsError NotFoundError Participant "
    "ParticipantRole ParticipantState Project PullRequest PullRequestComment PullRequestCreate "
    "PullRequestEndpoint PullRequestId PullRequestRendered PullRequestState PullRequestStatus "
    "PullRequestStatusCreate PullRequestStatusState PullRequestUpdate RateLimitError RenderedField Repository "
    "RepositorySlug RepositorySpec RetryPolicy ReviewerSpec Scm ServerError TransportError UserType Uuid "
    "ValidationError WorkspaceSlug __version__"
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
