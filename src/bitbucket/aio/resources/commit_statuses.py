from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.models.status import CommitStatusCreate
from bitbucket.models.status import CommitStatusUpdate
from bitbucket.models.status import PullRequestStatus
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport
    from bitbucket.ids import CommitHash
    from bitbucket.ids import RepositorySlug
    from bitbucket.ids import WorkspaceSlug


class AsyncCommitStatusesResource:
    # No `create`/`update`/`get`/`delete` matching AsyncNestedResource's shape: the
    # build-status item path is nested under a fixed "/build" segment
    # (.../statuses/build/{key}) rather than {path}/{id} — hand-written per the
    # over-abstraction guard in docs/TECH_SPEC.md.
    def __init__(self, transport: AsyncTransport, workspace: WorkspaceSlug, repository: RepositorySlug) -> None:
        self._transport = transport
        self._base_path = f"/repositories/{workspace}/{repository}"

    # GET .../commit/{commit}/statuses (auto-paginating)
    def list(self, commit: CommitHash | str) -> AsyncIterator[PullRequestStatus]:
        return apaginate(lambda cursor: self.list_page(commit, cursor=cursor))

    # GET .../commit/{commit}/statuses
    async def list_page(
        self, commit: CommitHash | str, *, cursor: str | None = None, pagelen: int = 100
    ) -> Page[PullRequestStatus]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._base_path}/commit/{commit}/statuses"
            data = await self._transport.request("GET", path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), PullRequestStatus)

    # POST .../commit/{commit}/statuses/build
    async def create(self, commit: CommitHash | str, payload: CommitStatusCreate) -> PullRequestStatus:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        path = f"{self._base_path}/commit/{commit}/statuses/build"
        data = await self._transport.request("POST", path, kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body)
        return PullRequestStatus.model_validate(data)

    # GET .../commit/{commit}/statuses/build/{key}
    async def get(self, commit: CommitHash | str, key: str) -> PullRequestStatus:
        data = await self._transport.request("GET", self._item_path(commit, key), kind=CqsKind.QUERY)
        return PullRequestStatus.model_validate(data)

    # PUT .../commit/{commit}/statuses/build/{key}
    async def update(self, commit: CommitHash | str, key: str, payload: CommitStatusUpdate) -> PullRequestStatus:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request(
            "PUT", self._item_path(commit, key), kind=CqsKind.IDEMPOTENT_COMMAND, json=body
        )
        return PullRequestStatus.model_validate(data)

    def _item_path(self, commit: CommitHash | str, key: str) -> str:
        return f"{self._base_path}/commit/{commit}/statuses/build/{key}"
