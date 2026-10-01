from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.models.account import Account
from bitbucket.models.account import DefaultReviewer
from bitbucket.models.account import DefaultReviewerAndType
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport
    from bitbucket.ids import ProjectKey
    from bitbucket.ids import RepositorySlug
    from bitbucket.ids import WorkspaceSlug


class AsyncDefaultReviewersResource:
    # {id} item path uses {target_username}, not {account_id} — see the note in
    # docs/api/endpoint-coverage.md — and has no create/update body, so it doesn't fit
    # AsyncNestedResource's {path}/{id} shape — hand-written per the
    # over-abstraction guard in docs/TECH_SPEC.md.
    def __init__(self, transport: AsyncTransport, workspace: WorkspaceSlug, repository: RepositorySlug) -> None:
        self._transport = transport
        self._base_path = f"/repositories/{workspace}/{repository}"
        self._path = f"{self._base_path}/default-reviewers"

    # GET {path} (auto-paginating)
    def list(self) -> AsyncIterator[DefaultReviewer]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    async def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[DefaultReviewer]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), DefaultReviewer)

    # GET {path}/{target_username}
    async def get(self, target_username: str) -> DefaultReviewer:
        data = await self._transport.request("GET", f"{self._path}/{target_username}", kind=CqsKind.QUERY)
        return DefaultReviewer.model_validate(data)

    # PUT {path}/{target_username}
    async def add(self, target_username: str) -> DefaultReviewer:
        data = await self._transport.request("PUT", f"{self._path}/{target_username}", kind=CqsKind.IDEMPOTENT_COMMAND)
        return DefaultReviewer.model_validate(data)

    # DELETE {path}/{target_username}
    async def remove(self, target_username: str) -> None:
        await self._transport.request("DELETE", f"{self._path}/{target_username}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET .../effective-default-reviewers (auto-paginating)
    def effective(self) -> AsyncIterator[DefaultReviewer]:
        return apaginate(lambda cursor: self.effective_page(cursor=cursor))

    # GET .../effective-default-reviewers
    async def effective_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[DefaultReviewer]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._base_path}/effective-default-reviewers"
            data = await self._transport.request("GET", path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), DefaultReviewer)


class AsyncProjectDefaultReviewersResource:
    # Keyed by {selected_user}; the list answers `{type, reviewer_type, user}`
    # wrappers while an item answers a bare user, so neither reuses the
    # repository resource's models. A project has no effective-reviewers path.
    def __init__(self, transport: AsyncTransport, workspace: WorkspaceSlug, project: ProjectKey) -> None:
        self._transport = transport
        self._path = f"/workspaces/{workspace}/projects/{project}/default-reviewers"

    # GET {path} (auto-paginating)
    def list(self) -> AsyncIterator[DefaultReviewerAndType]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    async def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[DefaultReviewerAndType]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), DefaultReviewerAndType)

    # GET {path}/{selected_user}
    async def get(self, selected_user: str) -> Account:
        data = await self._transport.request("GET", f"{self._path}/{selected_user}", kind=CqsKind.QUERY)
        return Account.model_validate(data)

    # PUT {path}/{selected_user}
    async def add(self, selected_user: str) -> Account:
        data = await self._transport.request("PUT", f"{self._path}/{selected_user}", kind=CqsKind.IDEMPOTENT_COMMAND)
        return Account.model_validate(data)

    # DELETE {path}/{selected_user}
    async def remove(self, selected_user: str) -> None:
        await self._transport.request("DELETE", f"{self._path}/{selected_user}", kind=CqsKind.IDEMPOTENT_COMMAND)
