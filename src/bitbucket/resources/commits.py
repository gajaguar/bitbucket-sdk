from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.account import Account
from bitbucket.models.commit import Commit
from bitbucket.models.diffstat import DiffStat
from bitbucket.resources.base import page_from_payload
from bitbucket.resources.comments import CommitCommentsResource
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport
    from bitbucket.ids import CommitHash


class CommitsResource:
    # None of these fit NestedResource's {path}/{id} shape: the collection is
    # `/commits` (plural) but the item path is `/commit/{hash}` (singular),
    # and diff/diffstat/patch/merge-base live under their own top-level paths
    # keyed by a revspec, not `/commits/{id}` — hand-written per the
    # over-abstraction guard in docs/TECH_SPEC.md.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._base_path = base_path

    # POST .../commit/{commit}/approve
    def approve(self, commit: CommitHash | str) -> Account:
        path = f"{self._base_path}/commit/{commit}/approve"
        data = self._transport.request("POST", path, kind=CqsKind.IDEMPOTENT_COMMAND)
        return Account.model_validate(data)

    def comments(self, commit: CommitHash | str) -> CommitCommentsResource:
        return CommitCommentsResource(self._transport, f"{self._base_path}/commit/{commit}")

    # GET .../diff/{spec}
    def diff(self, spec: str) -> str:
        return self._transport.request_text("GET", f"{self._base_path}/diff/{spec}", kind=CqsKind.QUERY)

    # GET .../diffstat/{spec} (auto-paginating)
    def diffstat(self, spec: str) -> Iterator[DiffStat]:
        return paginate(lambda cursor: self._diffstat_page(spec, cursor=cursor))

    def _diffstat_page(self, spec: str, *, cursor: str | None) -> Page[DiffStat]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", f"{self._base_path}/diffstat/{spec}", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), DiffStat)

    # GET .../commit/{commit}
    def get(self, commit: CommitHash | str) -> Commit:
        data = self._transport.request("GET", f"{self._base_path}/commit/{commit}", kind=CqsKind.QUERY)
        return Commit.model_validate(data)

    # GET .../commits (auto-paginating)
    def list(self, *, include: str | None = None, exclude: str | None = None) -> Iterator[Commit]:
        return paginate(lambda cursor: self.list_page(cursor=cursor, include=include, exclude=exclude))

    # GET .../commits
    def list_page(
        self,
        *,
        cursor: str | None = None,
        include: str | None = None,
        exclude: str | None = None,
        pagelen: int = 100,
    ) -> Page[Commit]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            params = {"pagelen": pagelen, "include": include, "exclude": exclude}
            data = self._transport.request("GET", f"{self._base_path}/commits", kind=CqsKind.QUERY, params=params)
        return page_from_payload(cast("dict[str, Any]", data), Commit)

    # GET .../commits/{revision} (auto-paginating) — commits reachable from `revision`
    def list_from(self, revision: str) -> Iterator[Commit]:
        return paginate(lambda cursor: self._list_from_page(revision, cursor=cursor))

    def _list_from_page(self, revision: str, *, cursor: str | None) -> Page[Commit]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", f"{self._base_path}/commits/{revision}", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Commit)

    # GET .../merge-base/{spec}
    def merge_base(self, spec: str) -> Commit:
        data = self._transport.request("GET", f"{self._base_path}/merge-base/{spec}", kind=CqsKind.QUERY)
        return Commit.model_validate(data)

    # GET .../patch/{spec}
    def patch(self, spec: str) -> str:
        return self._transport.request_text("GET", f"{self._base_path}/patch/{spec}", kind=CqsKind.QUERY)

    # DELETE .../commit/{commit}/approve
    def unapprove(self, commit: CommitHash | str) -> None:
        path = f"{self._base_path}/commit/{commit}/approve"
        self._transport.request("DELETE", path, kind=CqsKind.IDEMPOTENT_COMMAND)
