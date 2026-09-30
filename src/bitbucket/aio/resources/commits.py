from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.aio.resources.comments import AsyncCommitCommentsResource
from bitbucket.models.account import Account
from bitbucket.models.commit import Commit
from bitbucket.models.diffstat import DiffStat
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport
    from bitbucket.ids import CommitHash


class AsyncCommitsResource:
    # None of these fit AsyncNestedResource's {path}/{id} shape: the collection is
    # `/commits` (plural) but the item path is `/commit/{hash}` (singular),
    # and diff/diffstat/patch/merge-base live under their own top-level paths
    # keyed by a revspec, not `/commits/{id}` — hand-written per the
    # over-abstraction guard in docs/TECH_SPEC.md.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._base_path = base_path

    # POST .../commit/{commit}/approve
    async def approve(self, commit: CommitHash | str) -> Account:
        path = f"{self._base_path}/commit/{commit}/approve"
        data = await self._transport.request("POST", path, kind=CqsKind.IDEMPOTENT_COMMAND)
        return Account.model_validate(data)

    def comments(self, commit: CommitHash | str) -> AsyncCommitCommentsResource:
        return AsyncCommitCommentsResource(self._transport, f"{self._base_path}/commit/{commit}")

    # GET .../diff/{spec}
    async def diff(self, spec: str) -> str:
        return await self._transport.request_text("GET", f"{self._base_path}/diff/{spec}", kind=CqsKind.QUERY)

    # GET .../diffstat/{spec} (auto-paginating)
    def diffstat(self, spec: str) -> AsyncIterator[DiffStat]:
        return apaginate(lambda cursor: self._diffstat_page(spec, cursor=cursor))

    async def _diffstat_page(self, spec: str, *, cursor: str | None) -> Page[DiffStat]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request("GET", f"{self._base_path}/diffstat/{spec}", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), DiffStat)

    # GET .../commit/{commit}
    async def get(self, commit: CommitHash | str) -> Commit:
        data = await self._transport.request("GET", f"{self._base_path}/commit/{commit}", kind=CqsKind.QUERY)
        return Commit.model_validate(data)

    # GET .../commits (auto-paginating)
    def list(self, *, include: str | None = None, exclude: str | None = None) -> AsyncIterator[Commit]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor, include=include, exclude=exclude))

    # GET .../commits
    async def list_page(
        self,
        *,
        cursor: str | None = None,
        include: str | None = None,
        exclude: str | None = None,
        pagelen: int = 100,
    ) -> Page[Commit]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            params = {"pagelen": pagelen, "include": include, "exclude": exclude}
            data = await self._transport.request(
                "GET", f"{self._base_path}/commits", kind=CqsKind.QUERY, params=params
            )
        return page_from_payload(cast("dict[str, Any]", data), Commit)

    # GET .../commits/{revision} (auto-paginating) — commits reachable from `revision`
    def list_from(self, revision: str) -> AsyncIterator[Commit]:
        return apaginate(lambda cursor: self._list_from_page(revision, cursor=cursor))

    async def _list_from_page(self, revision: str, *, cursor: str | None) -> Page[Commit]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request("GET", f"{self._base_path}/commits/{revision}", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Commit)

    # GET .../merge-base/{spec}
    async def merge_base(self, spec: str) -> Commit:
        data = await self._transport.request("GET", f"{self._base_path}/merge-base/{spec}", kind=CqsKind.QUERY)
        return Commit.model_validate(data)

    # GET .../patch/{spec}
    async def patch(self, spec: str) -> str:
        return await self._transport.request_text("GET", f"{self._base_path}/patch/{spec}", kind=CqsKind.QUERY)

    # DELETE .../commit/{commit}/approve
    async def unapprove(self, commit: CommitHash | str) -> None:
        path = f"{self._base_path}/commit/{commit}/approve"
        await self._transport.request("DELETE", path, kind=CqsKind.IDEMPOTENT_COMMAND)
