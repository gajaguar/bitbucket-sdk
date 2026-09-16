from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket.models.account import Account
from bitbucket.models.pull_request import PullRequest
from bitbucket.models.pull_request import PullRequestCreate
from bitbucket.models.pull_request import PullRequestUpdate
from bitbucket.resources.base import NestedResource
from bitbucket.resources.comments import CommentsResource
from bitbucket.resources.statuses import StatusesResource
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from bitbucket._transport import Transport
    from bitbucket.ids import PullRequestId
    from bitbucket.ids import RepositorySlug
    from bitbucket.ids import WorkspaceSlug


class PullRequestsResource(NestedResource[PullRequest, PullRequestCreate, PullRequestUpdate]):
    # No `delete`: Bitbucket has no DELETE-by-id endpoint for pull requests (they are
    # merged, declined, or superseded, never removed) — see DeletableResourceMixin's
    # docstring in resources/base.py for the resource that does need it.
    _path = "/pullrequests"
    _read_model = PullRequest

    def __init__(self, transport: Transport, workspace: WorkspaceSlug, repository: RepositorySlug) -> None:
        super().__init__(transport, f"/repositories/{workspace}/{repository}")

    # POST {path}/{id}/approve
    def approve(self, pull_request_id: PullRequestId | int) -> Account:
        data = self._transport.request(
            "POST", f"{self._item_path(pull_request_id)}/approve", kind=CqsKind.IDEMPOTENT_COMMAND
        )
        return Account.model_validate(data)

    def comments(self, pull_request_id: PullRequestId | int) -> CommentsResource:
        return CommentsResource(self._transport, self._item_path(pull_request_id))

    # GET {path}/{id}/diff
    def diff(self, pull_request_id: PullRequestId | int) -> str:
        return self._transport.request_text("GET", f"{self._item_path(pull_request_id)}/diff", kind=CqsKind.QUERY)

    def statuses(self, pull_request_id: PullRequestId | int) -> StatusesResource:
        return StatusesResource(self._transport, self._item_path(pull_request_id))
