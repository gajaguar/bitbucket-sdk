from __future__ import annotations

from typing import NewType

WorkspaceSlug = NewType("WorkspaceSlug", str)  # pylint: disable=app-module-const-naming,app-require-final
RepositorySlug = NewType("RepositorySlug", str)  # pylint: disable=app-module-const-naming,app-require-final
PullRequestId = NewType("PullRequestId", int)  # pylint: disable=app-module-const-naming,app-require-final
CommentId = NewType("CommentId", int)  # pylint: disable=app-module-const-naming,app-require-final
AccountId = NewType("AccountId", str)  # pylint: disable=app-module-const-naming,app-require-final
Uuid = NewType("Uuid", str)  # pylint: disable=app-module-const-naming,app-require-final
CommitHash = NewType("CommitHash", str)  # pylint: disable=app-module-const-naming,app-require-final
TaskId = NewType("TaskId", int)  # pylint: disable=app-module-const-naming,app-require-final
