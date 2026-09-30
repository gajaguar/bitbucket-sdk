from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.models.status import PullRequestStatus
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport


class AsyncStatusesResource:
    # Read-only, nested under a pull request — hand-written rather than
    # AsyncNestedResource, per the over-abstraction guard in docs/TECH_SPEC.md.
    def __init__(self, transport: AsyncTransport, pull_request_path: str) -> None:
        self._transport = transport
        self._pull_request_path = pull_request_path

    # GET {pr_path}/statuses (auto-paginating)
    def list(self) -> AsyncIterator[PullRequestStatus]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {pr_path}/statuses
    async def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[PullRequestStatus]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request(
                "GET", f"{self._pull_request_path}/statuses", kind=CqsKind.QUERY, params={"pagelen": pagelen}
            )
        return page_from_payload(cast("dict[str, Any]", data), PullRequestStatus)
