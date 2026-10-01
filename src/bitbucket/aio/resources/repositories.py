from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.aio.resources.hooks import AsyncHooksResource
from bitbucket.aio.resources.permissions import AsyncRepositoryPermissionsResource
from bitbucket.models.account import Account
from bitbucket.models.activity import Activity
from bitbucket.models.pull_request import PullRequest
from bitbucket.models.repository import ForkCreate
from bitbucket.models.repository import Repository
from bitbucket.models.repository import RepositoryCreate
from bitbucket.models.repository import RepositoryUpdate
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport
    from bitbucket.ids import CommitHash
    from bitbucket.ids import RepositorySlug
    from bitbucket.ids import WorkspaceSlug


class AsyncRepositoriesResource:
    # Workspace-scoped, with no per-repo {id} nesting a create/update/delete
    # could hang off in AsyncNestedResource's shape: create puts the slug in the
    # *path*, not the body (see the note in docs/api/endpoint-coverage.md) — hand-written
    # per the over-abstraction guard in docs/TECH_SPEC.md.
    def __init__(self, transport: AsyncTransport, workspace: WorkspaceSlug) -> None:
        self._transport = transport
        self._workspace = workspace

    # POST .../repositories/{workspace}/{repo_slug}
    async def create(self, slug: RepositorySlug | str, payload: RepositoryCreate) -> Repository:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request(
            "POST", self._item_path(slug), kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body
        )
        return Repository.model_validate(data)

    # DELETE .../repositories/{workspace}/{repo_slug}
    async def delete(self, slug: RepositorySlug | str) -> None:
        await self._transport.request("DELETE", self._item_path(slug), kind=CqsKind.IDEMPOTENT_COMMAND)

    # POST .../repositories/{workspace}/{repo_slug}/forks
    async def create_fork(self, slug: RepositorySlug | str, payload: ForkCreate | None = None) -> Repository:
        body = (payload or ForkCreate()).model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request(
            "POST", f"{self._item_path(slug)}/forks", kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body
        )
        return Repository.model_validate(data)

    # GET .../repositories/{workspace}/{repo_slug}/forks (auto-paginating)
    def forks(self, slug: RepositorySlug | str) -> AsyncIterator[Repository]:
        return apaginate(lambda cursor: self.forks_page(slug, cursor=cursor))

    # GET .../repositories/{workspace}/{repo_slug}/forks
    async def forks_page(self, slug: RepositorySlug | str, *, cursor: str | None = None) -> Page[Repository]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request("GET", f"{self._item_path(slug)}/forks", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Repository)

    # GET .../repositories/{workspace}/{repo_slug}
    async def get(self, slug: RepositorySlug | str) -> Repository:
        data = await self._transport.request("GET", self._item_path(slug), kind=CqsKind.QUERY)
        return Repository.model_validate(data)

    def hooks(self, slug: RepositorySlug | str) -> AsyncHooksResource:
        return AsyncHooksResource(self._transport, self._item_path(slug))

    # GET .../repositories/{workspace} (auto-paginating)
    def list(self, *, q: str | None = None, sort: str | None = None) -> AsyncIterator[Repository]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor, q=q, sort=sort))

    # GET .../repositories/{workspace}
    async def list_page(
        self,
        *,
        cursor: str | None = None,
        q: str | None = None,
        sort: str | None = None,
        pagelen: int = 100,
    ) -> Page[Repository]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            params: dict[str, Any] = {"pagelen": pagelen, "q": q, "sort": sort}
            data = await self._transport.request("GET", self._collection_path(), kind=CqsKind.QUERY, params=params)
        return page_from_payload(cast("dict[str, Any]", data), Repository)

    def permissions(self, slug: RepositorySlug | str) -> AsyncRepositoryPermissionsResource:
        return AsyncRepositoryPermissionsResource(self._transport, self._item_path(slug))

    # PUT .../repositories/{workspace}/{repo_slug}
    async def update(self, slug: RepositorySlug | str, payload: RepositoryUpdate) -> Repository:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request("PUT", self._item_path(slug), kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
        return Repository.model_validate(data)

    # GET .../repositories/{workspace}/{repo_slug}/watchers (auto-paginating)
    def watchers(self, slug: RepositorySlug | str) -> AsyncIterator[Account]:
        return apaginate(lambda cursor: self.watchers_page(slug, cursor=cursor))

    # GET .../repositories/{workspace}/{repo_slug}/watchers
    async def watchers_page(self, slug: RepositorySlug | str, *, cursor: str | None = None) -> Page[Account]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request("GET", f"{self._item_path(slug)}/watchers", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Account)

    # GET .../commit/{commit}/pullrequests (auto-paginating)
    def commit_pull_requests(self, slug: RepositorySlug | str, commit: CommitHash | str) -> AsyncIterator[PullRequest]:
        return apaginate(lambda cursor: self.commit_pull_requests_page(slug, commit, cursor=cursor))

    # GET .../commit/{commit}/pullrequests
    async def commit_pull_requests_page(
        self, slug: RepositorySlug | str, commit: CommitHash | str, *, cursor: str | None = None
    ) -> Page[PullRequest]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._item_path(slug)}/commit/{commit}/pullrequests"
            data = await self._transport.request("GET", path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), PullRequest)

    # GET .../pullrequests/activity (auto-paginating)
    def pull_request_activity(self, slug: RepositorySlug | str) -> AsyncIterator[Activity]:
        return apaginate(lambda cursor: self.pull_request_activity_page(slug, cursor=cursor))

    # GET .../pullrequests/activity
    async def pull_request_activity_page(
        self, slug: RepositorySlug | str, *, cursor: str | None = None
    ) -> Page[Activity]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._item_path(slug)}/pullrequests/activity"
            data = await self._transport.request("GET", path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Activity)

    def _collection_path(self) -> str:
        return f"/repositories/{self._workspace}"

    def _item_path(self, slug: RepositorySlug | str) -> str:
        return f"{self._collection_path()}/{slug}"
