from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final
from typing import cast

from bitbucket._pagination import paginate
from bitbucket._polling import poll_until_terminal
from bitbucket.models.account import Account
from bitbucket.models.activity import Activity
from bitbucket.models.commit import Commit
from bitbucket.models.conflict import FileConflict
from bitbucket.models.diffstat import DiffStat
from bitbucket.models.merge import MergeParameters
from bitbucket.models.merge import MergeTask
from bitbucket.models.merge import MergeTaskState
from bitbucket.models.merge import MergeTaskStatus
from bitbucket.models.pull_request import PullRequest
from bitbucket.models.pull_request import PullRequestCreate
from bitbucket.models.pull_request import PullRequestUpdate
from bitbucket.resources.base import NestedResource
from bitbucket.resources.base import page_from_payload
from bitbucket.resources.comments import CommentsResource
from bitbucket.resources.properties import PropertiesResource
from bitbucket.resources.statuses import StatusesResource
from bitbucket.resources.tasks import TasksResource
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport
    from bitbucket.ids import PullRequestId
    from bitbucket.ids import RepositorySlug
    from bitbucket.ids import WorkspaceSlug

_TERMINAL_MERGE_STATES: Final = frozenset({MergeTaskState.SUCCESS, MergeTaskState.FAILED})


class PullRequestsResource(NestedResource[PullRequest, PullRequestCreate, PullRequestUpdate]):
    # No `delete`: Bitbucket has no DELETE-by-id endpoint for pull requests (they are
    # merged, declined, or superseded, never removed) — see DeletableResourceMixin's
    # docstring in resources/base.py for the resource that does need it.
    _path = "/pullrequests"
    _read_model = PullRequest

    def __init__(self, transport: Transport, workspace: WorkspaceSlug, repository: RepositorySlug) -> None:
        super().__init__(transport, f"/repositories/{workspace}/{repository}")

    # GET {path}/{id}/activity (auto-paginating)
    def activity(self, pull_request_id: PullRequestId | int) -> Iterator[Activity]:
        return paginate(lambda cursor: self._activity_page(pull_request_id, cursor=cursor))

    def _activity_page(self, pull_request_id: PullRequestId | int, *, cursor: str | None) -> Page[Activity]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._item_path(pull_request_id)}/activity"
            data = self._transport.request("GET", path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Activity)

    # POST {path}/{id}/approve
    def approve(self, pull_request_id: PullRequestId | int) -> Account:
        data = self._transport.request(
            "POST", f"{self._item_path(pull_request_id)}/approve", kind=CqsKind.IDEMPOTENT_COMMAND
        )
        return Account.model_validate(data)

    def comments(self, pull_request_id: PullRequestId | int) -> CommentsResource:
        return CommentsResource(self._transport, self._item_path(pull_request_id))

    # GET {path}/{id}/commits (auto-paginating)
    def commits(self, pull_request_id: PullRequestId | int) -> Iterator[Commit]:
        return paginate(lambda cursor: self._commits_page(pull_request_id, cursor=cursor))

    def _commits_page(self, pull_request_id: PullRequestId | int, *, cursor: str | None) -> Page[Commit]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._item_path(pull_request_id)}/commits"
            data = self._transport.request("GET", path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Commit)

    # GET {path}/{id}/conflicts (auto-paginating)
    def conflicts(self, pull_request_id: PullRequestId | int) -> Iterator[FileConflict]:
        return paginate(lambda cursor: self._conflicts_page(pull_request_id, cursor=cursor))

    def _conflicts_page(self, pull_request_id: PullRequestId | int, *, cursor: str | None) -> Page[FileConflict]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._item_path(pull_request_id)}/conflicts"
            data = self._transport.request("GET", path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), FileConflict)

    # POST {path}/{id}/decline
    def decline(self, pull_request_id: PullRequestId | int) -> PullRequest:
        data = self._transport.request(
            "POST", f"{self._item_path(pull_request_id)}/decline", kind=CqsKind.IDEMPOTENT_COMMAND
        )
        return PullRequest.model_validate(data)

    # GET {path}/{id}/diff
    def diff(self, pull_request_id: PullRequestId | int) -> str:
        return self._transport.request_text("GET", f"{self._item_path(pull_request_id)}/diff", kind=CqsKind.QUERY)

    # GET {path}/{id}/diffstat (auto-paginating)
    def diffstat(self, pull_request_id: PullRequestId | int) -> Iterator[DiffStat]:
        return paginate(lambda cursor: self._diffstat_page(pull_request_id, cursor=cursor))

    def _diffstat_page(self, pull_request_id: PullRequestId | int, *, cursor: str | None) -> Page[DiffStat]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._item_path(pull_request_id)}/diffstat"
            data = self._transport.request("GET", path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), DiffStat)

    # POST {path}/{id}/merge
    def merge(self, pull_request_id: PullRequestId | int, payload: MergeParameters | None = None) -> MergeTask:
        body = (payload or MergeParameters()).model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request(
            "POST", f"{self._item_path(pull_request_id)}/merge", kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body
        )
        return MergeTask.model_validate(data)

    # GET {path}/{id}/merge/task-status/{task_id}
    def merge_task_status(self, pull_request_id: PullRequestId | int, task_id: str) -> MergeTaskStatus:
        path = f"{self._item_path(pull_request_id)}/merge/task-status/{task_id}"
        data = self._transport.request("GET", path, kind=CqsKind.QUERY)
        return MergeTaskStatus.model_validate(data)

    def merge_and_wait(
        self,
        pull_request_id: PullRequestId | int,
        payload: MergeParameters | None = None,
        *,
        timeout: float = 60.0,
        interval: float = 1.0,
        sleep: Callable[[float], None] | None = None,
    ) -> MergeTaskStatus:
        task = self.merge(pull_request_id, payload)
        poll_kwargs = {} if sleep is None else {"sleep": sleep}
        return poll_until_terminal(
            lambda: self.merge_task_status(pull_request_id, cast("str", task.task_id)),
            is_terminal=lambda status: status.task_status in _TERMINAL_MERGE_STATES,
            timeout=timeout,
            interval=interval,
            **poll_kwargs,
        )

    # GET {path}/{id}/patch
    def patch(self, pull_request_id: PullRequestId | int) -> str:
        return self._transport.request_text("GET", f"{self._item_path(pull_request_id)}/patch", kind=CqsKind.QUERY)

    def properties(self, pull_request_id: PullRequestId | int) -> PropertiesResource:
        return PropertiesResource(self._transport, self._item_path(pull_request_id))

    # POST {path}/{id}/request-changes
    def request_changes(self, pull_request_id: PullRequestId | int) -> Account:
        data = self._transport.request(
            "POST", f"{self._item_path(pull_request_id)}/request-changes", kind=CqsKind.IDEMPOTENT_COMMAND
        )
        return Account.model_validate(data)

    def statuses(self, pull_request_id: PullRequestId | int) -> StatusesResource:
        return StatusesResource(self._transport, self._item_path(pull_request_id))

    def tasks(self, pull_request_id: PullRequestId | int) -> TasksResource:
        return TasksResource(self._transport, self._item_path(pull_request_id))

    # DELETE {path}/{id}/approve
    def unapprove(self, pull_request_id: PullRequestId | int) -> None:
        self._transport.request(
            "DELETE", f"{self._item_path(pull_request_id)}/approve", kind=CqsKind.IDEMPOTENT_COMMAND
        )

    # DELETE {path}/{id}/request-changes
    def unrequest_changes(self, pull_request_id: PullRequestId | int) -> None:
        self._transport.request(
            "DELETE", f"{self._item_path(pull_request_id)}/request-changes", kind=CqsKind.IDEMPOTENT_COMMAND
        )
