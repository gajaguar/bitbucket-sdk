from __future__ import annotations

from bitbucket.aio.resources.base import AsyncDeletableResourceMixin
from bitbucket.aio.resources.base import AsyncNestedResource
from bitbucket.models.comment import CommentCreate
from bitbucket.models.comment import CommentUpdate
from bitbucket.models.comment import PullRequestComment
from bitbucket.retry import CqsKind


class AsyncCommentsResource(
    AsyncNestedResource[PullRequestComment, CommentCreate, CommentUpdate],
    AsyncDeletableResourceMixin,
):
    _path = "/comments"
    _read_model = PullRequestComment

    # POST {path}/{id}/resolve
    async def resolve(self, comment_id: object) -> PullRequestComment:
        data = await self._transport.request(
            "POST", f"{self._item_path(comment_id)}/resolve", kind=CqsKind.IDEMPOTENT_COMMAND
        )
        return PullRequestComment.model_validate(data)

    # DELETE {path}/{id}/resolve
    async def unresolve(self, comment_id: object) -> None:
        await self._transport.request(
            "DELETE", f"{self._item_path(comment_id)}/resolve", kind=CqsKind.IDEMPOTENT_COMMAND
        )


class AsyncCommitCommentsResource(
    AsyncNestedResource[PullRequestComment, CommentCreate, CommentUpdate],
    AsyncDeletableResourceMixin,
):
    # Commit comments share pull-request comments' exact wire shape, but have
    # no resolve/unresolve endpoint — a separate class rather than an
    # AsyncCommentsResource subclass, so `.resolve()` isn't offered where
    # Bitbucket doesn't support it.
    _path = "/comments"
    _read_model = PullRequestComment
