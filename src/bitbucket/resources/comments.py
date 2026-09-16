from __future__ import annotations

from bitbucket.models.comment import CommentCreate
from bitbucket.models.comment import CommentUpdate
from bitbucket.models.comment import PullRequestComment
from bitbucket.resources.base import DeletableResourceMixin
from bitbucket.resources.base import NestedResource
from bitbucket.retry import CqsKind


class CommentsResource(NestedResource[PullRequestComment, CommentCreate, CommentUpdate], DeletableResourceMixin):
    _path = "/comments"
    _read_model = PullRequestComment

    # POST {path}/{id}/resolve
    def resolve(self, comment_id: object) -> PullRequestComment:
        data = self._transport.request(
            "POST", f"{self._item_path(comment_id)}/resolve", kind=CqsKind.IDEMPOTENT_COMMAND
        )
        return PullRequestComment.model_validate(data)

    # DELETE {path}/{id}/resolve
    def unresolve(self, comment_id: object) -> None:
        self._transport.request("DELETE", f"{self._item_path(comment_id)}/resolve", kind=CqsKind.IDEMPOTENT_COMMAND)
