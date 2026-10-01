from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket._polling import apoll_until_terminal
from bitbucket.aio.resources.base import AsyncNestedResource
from bitbucket.aio.resources.comments import AsyncCommentsResource
from bitbucket.aio.resources.properties import AsyncPropertiesResource
from bitbucket.aio.resources.statuses import AsyncStatusesResource
from bitbucket.aio.resources.tasks import AsyncTasksResource
from bitbucket.models.account import Account
from bitbucket.models.activity import Activity
from bitbucket.models.commit import Commit
from bitbucket.models.conflict import FileConflict
from bitbucket.models.diffstat import DiffStat
from bitbucket.models.merge import MergeParameters
from bitbucket.models.merge import MergeTask
from bitbucket.models.merge import MergeTaskState
from bitbucket.models.merge import MergeTaskStatus
from bitbucket.models.mergeability import MergeabilityCheck
from bitbucket.models.pull_request import PullRequest
from bitbucket.models.pull_request import PullRequestCreate
from bitbucket.models.pull_request import PullRequestUpdate
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from collections.abc import Awaitable
    from collections.abc import Callable
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport
    from bitbucket.ids import PullRequestId
    from bitbucket.ids import RepositorySlug
    from bitbucket.ids import WorkspaceSlug

_TERMINAL_MERGE_STATES: Final = frozenset({MergeTaskState.SUCCESS, MergeTaskState.FAILED})


class AsyncPullRequestsResource(
    AsyncNestedResource[PullRequest, PullRequestCreate, PullRequestUpdate],
):
    # No `delete`: Bitbucket has no DELETE-by-id endpoint for pull requests (they are
    # merged, declined, or superseded, never removed) — see AsyncDeletableResourceMixin's
    # docstring in resources/base.py for the resource that does need it.
    _path = "/pullrequests"
    _read_model = PullRequest

    def __init__(self, transport: AsyncTransport, workspace: WorkspaceSlug, repository: RepositorySlug) -> None:
        super().__init__(transport, f"/repositories/{workspace}/{repository}")

    # GET {path}/{id}/activity (auto-paginating)
    def activity(self, pull_request_id: PullRequestId | int) -> AsyncIterator[Activity]:
        return apaginate(lambda cursor: self.activity_page(pull_request_id, cursor=cursor))

    # GET {path}/{id}/activity
    async def activity_page(
        self, pull_request_id: PullRequestId | int, *, cursor: str | None = None
    ) -> Page[Activity]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._item_path(pull_request_id)}/activity"
            data = await self._transport.request("GET", path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Activity)

    # POST {path}/{id}/approve
    async def approve(self, pull_request_id: PullRequestId | int) -> Account:
        data = await self._transport.request(
            "POST", f"{self._item_path(pull_request_id)}/approve", kind=CqsKind.IDEMPOTENT_COMMAND
        )
        return Account.model_validate(data)

    def comments(self, pull_request_id: PullRequestId | int) -> AsyncCommentsResource:
        return AsyncCommentsResource(self._transport, self._item_path(pull_request_id))

    # GET {path}/{id}/commits (auto-paginating)
    def commits(self, pull_request_id: PullRequestId | int) -> AsyncIterator[Commit]:
        return apaginate(lambda cursor: self.commits_page(pull_request_id, cursor=cursor))

    # GET {path}/{id}/commits
    async def commits_page(self, pull_request_id: PullRequestId | int, *, cursor: str | None = None) -> Page[Commit]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._item_path(pull_request_id)}/commits"
            data = await self._transport.request("GET", path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Commit)

    # GET {path}/{id}/conflicts (auto-paginating)
    def conflicts(self, pull_request_id: PullRequestId | int) -> AsyncIterator[FileConflict]:
        return apaginate(lambda cursor: self.conflicts_page(pull_request_id, cursor=cursor))

    # GET {path}/{id}/conflicts
    async def conflicts_page(
        self, pull_request_id: PullRequestId | int, *, cursor: str | None = None
    ) -> Page[FileConflict]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._item_path(pull_request_id)}/conflicts"
            data = await self._transport.request("GET", path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), FileConflict)

    # POST {path}/{id}/decline
    async def decline(self, pull_request_id: PullRequestId | int) -> PullRequest:
        data = await self._transport.request(
            "POST", f"{self._item_path(pull_request_id)}/decline", kind=CqsKind.IDEMPOTENT_COMMAND
        )
        return PullRequest.model_validate(data)

    # GET {path}/{id}/diff
    async def diff(self, pull_request_id: PullRequestId | int) -> str:
        return await self._transport.request_text(
            "GET", f"{self._item_path(pull_request_id)}/diff", kind=CqsKind.QUERY
        )

    # GET {path}/{id}/diffstat (auto-paginating)
    def diffstat(self, pull_request_id: PullRequestId | int) -> AsyncIterator[DiffStat]:
        return apaginate(lambda cursor: self.diffstat_page(pull_request_id, cursor=cursor))

    # GET {path}/{id}/diffstat
    async def diffstat_page(
        self, pull_request_id: PullRequestId | int, *, cursor: str | None = None
    ) -> Page[DiffStat]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._item_path(pull_request_id)}/diffstat"
            data = await self._transport.request("GET", path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), DiffStat)

    # POST {path}/{id}/merge
    async def merge(self, pull_request_id: PullRequestId | int, payload: MergeParameters | None = None) -> MergeTask:
        body = (payload or MergeParameters()).model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request(
            "POST", f"{self._item_path(pull_request_id)}/merge", kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body
        )
        return MergeTask.model_validate(data)

    # GET {path}/{id}/merge/task-status/{task_id}
    async def merge_task_status(self, pull_request_id: PullRequestId | int, task_id: str) -> MergeTaskStatus:
        path = f"{self._item_path(pull_request_id)}/merge/task-status/{task_id}"
        data = await self._transport.request("GET", path, kind=CqsKind.QUERY)
        return MergeTaskStatus.model_validate(data)

    async def merge_and_wait(
        self,
        pull_request_id: PullRequestId | int,
        payload: MergeParameters | None = None,
        *,
        timeout: float = 60.0,  # ruff: ignore[async-function-with-timeout]
        interval: float = 1.0,
        sleep: Callable[[float], Awaitable[None]] | None = None,
    ) -> MergeTaskStatus:
        task = await self.merge(pull_request_id, payload)
        poll_kwargs = {} if sleep is None else {"sleep": sleep}
        return await apoll_until_terminal(
            lambda: self.merge_task_status(pull_request_id, cast("str", task.task_id)),
            is_terminal=lambda status: status.task_status in _TERMINAL_MERGE_STATES,
            timeout=timeout,
            interval=interval,
            **poll_kwargs,
        )

    # GET {path}/{id}/mergeability/checks
    async def mergeability_checks(
        self, pull_request_id: PullRequestId | int, *, q: str | None = None
    ) -> list[MergeabilityCheck]:
        path = f"{self._item_path(pull_request_id)}/mergeability/checks"
        data = await self._transport.request("GET", path, kind=CqsKind.QUERY, params={"q": q})
        return page_from_payload(cast("dict[str, Any]", data), MergeabilityCheck).items

    # GET {path}/{id}/patch
    async def patch(self, pull_request_id: PullRequestId | int) -> str:
        return await self._transport.request_text(
            "GET", f"{self._item_path(pull_request_id)}/patch", kind=CqsKind.QUERY
        )

    def properties(self, pull_request_id: PullRequestId | int) -> AsyncPropertiesResource:
        return AsyncPropertiesResource(self._transport, self._item_path(pull_request_id))

    # POST {path}/{id}/request-changes
    async def request_changes(self, pull_request_id: PullRequestId | int) -> Account:
        data = await self._transport.request(
            "POST", f"{self._item_path(pull_request_id)}/request-changes", kind=CqsKind.IDEMPOTENT_COMMAND
        )
        return Account.model_validate(data)

    def statuses(self, pull_request_id: PullRequestId | int) -> AsyncStatusesResource:
        return AsyncStatusesResource(self._transport, self._item_path(pull_request_id))

    def tasks(self, pull_request_id: PullRequestId | int) -> AsyncTasksResource:
        return AsyncTasksResource(self._transport, self._item_path(pull_request_id))

    # DELETE {path}/{id}/approve
    async def unapprove(self, pull_request_id: PullRequestId | int) -> None:
        await self._transport.request(
            "DELETE", f"{self._item_path(pull_request_id)}/approve", kind=CqsKind.IDEMPOTENT_COMMAND
        )

    # DELETE {path}/{id}/request-changes
    async def unrequest_changes(self, pull_request_id: PullRequestId | int) -> None:
        await self._transport.request(
            "DELETE", f"{self._item_path(pull_request_id)}/request-changes", kind=CqsKind.IDEMPOTENT_COMMAND
        )
