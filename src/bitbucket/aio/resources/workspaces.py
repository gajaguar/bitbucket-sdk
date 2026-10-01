from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.models.permission import RepositoryPermission
from bitbucket.models.workspace import WorkspaceMembership
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport


class AsyncWorkspaceMembersResource:
    # Read-only and keyed by a member UUID or Atlassian account id, so it does
    # not fit NestedResource's create/update shape — hand-written.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/members"

    # GET {path} (auto-paginating)
    def list(self) -> AsyncIterator[WorkspaceMembership]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    async def list_page(self, *, cursor: str | None = None) -> Page[WorkspaceMembership]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request("GET", self._path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), WorkspaceMembership)

    # GET {path}/{member}
    async def get(self, member: str) -> WorkspaceMembership:
        data = await self._transport.request("GET", f"{self._path}/{member}", kind=CqsKind.QUERY)
        return WorkspaceMembership.model_validate(data)


class AsyncWorkspacePermissionsResource:
    # Effective permissions only (no direct/group split), all read-only.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/permissions"

    # GET {path} (auto-paginating)
    def list(self, *, q: str | None = None) -> AsyncIterator[WorkspaceMembership]:
        return apaginate(lambda cursor: self.list_page(q=q, cursor=cursor))

    # GET {path}
    async def list_page(self, *, q: str | None = None, cursor: str | None = None) -> Page[WorkspaceMembership]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"q": q})
        return page_from_payload(cast("dict[str, Any]", data), WorkspaceMembership)

    # GET {path}/repositories (auto-paginating)
    def repositories(self, *, q: str | None = None, sort: str | None = None) -> AsyncIterator[RepositoryPermission]:
        return apaginate(lambda cursor: self.repositories_page(q=q, sort=sort, cursor=cursor))

    # GET {path}/repositories
    async def repositories_page(
        self,
        *,
        q: str | None = None,
        sort: str | None = None,
        cursor: str | None = None,
    ) -> Page[RepositoryPermission]:
        return await self._repository_permissions_page(f"{self._path}/repositories", q=q, sort=sort, cursor=cursor)

    # GET {path}/repositories/{repo_slug} (auto-paginating)
    def repository(
        self,
        repo_slug: str,
        *,
        q: str | None = None,
        sort: str | None = None,
    ) -> AsyncIterator[RepositoryPermission]:
        return apaginate(lambda cursor: self.repository_page(repo_slug, q=q, sort=sort, cursor=cursor))

    # GET {path}/repositories/{repo_slug}
    async def repository_page(
        self,
        repo_slug: str,
        *,
        q: str | None = None,
        sort: str | None = None,
        cursor: str | None = None,
    ) -> Page[RepositoryPermission]:
        return await self._repository_permissions_page(
            f"{self._path}/repositories/{repo_slug}", q=q, sort=sort, cursor=cursor
        )

    async def _repository_permissions_page(
        self,
        path: str,
        *,
        q: str | None,
        sort: str | None,
        cursor: str | None,
    ) -> Page[RepositoryPermission]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request("GET", path, kind=CqsKind.QUERY, params={"q": q, "sort": sort})
        return page_from_payload(cast("dict[str, Any]", data), RepositoryPermission)
