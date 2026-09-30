from __future__ import annotations

from typing import NewType

WorkspaceSlug = NewType("WorkspaceSlug", str)  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
RepositorySlug = NewType("RepositorySlug", str)  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
PullRequestId = NewType("PullRequestId", int)  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
CommentId = NewType("CommentId", int)  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
AccountId = NewType("AccountId", str)  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
Uuid = NewType("Uuid", str)  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
CommitHash = NewType("CommitHash", str)  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
TaskId = NewType("TaskId", int)  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
