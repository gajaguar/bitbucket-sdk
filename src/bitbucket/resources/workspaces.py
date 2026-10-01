from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.permission import RepositoryPermission
from bitbucket.models.workspace import WorkspaceMembership
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport


class WorkspaceMembersResource:
    # Read-only and keyed by a member UUID or Atlassian account id, so it does
    # not fit NestedResource's create/update shape — hand-written.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/members"

    # GET {path} (auto-paginating)
    def list(self) -> Iterator[WorkspaceMembership]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    def list_page(self, *, cursor: str | None = None) -> Page[WorkspaceMembership]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", self._path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), WorkspaceMembership)

    # GET {path}/{member}
    def get(self, member: str) -> WorkspaceMembership:
        data = self._transport.request("GET", f"{self._path}/{member}", kind=CqsKind.QUERY)
        return WorkspaceMembership.model_validate(data)


class WorkspacePermissionsResource:
    # Effective permissions only (no direct/group split), all read-only.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/permissions"

    # GET {path} (auto-paginating)
    def list(self, *, q: str | None = None) -> Iterator[WorkspaceMembership]:
        return paginate(lambda cursor: self.list_page(q=q, cursor=cursor))

    # GET {path}
    def list_page(self, *, q: str | None = None, cursor: str | None = None) -> Page[WorkspaceMembership]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"q": q})
        return page_from_payload(cast("dict[str, Any]", data), WorkspaceMembership)

    # GET {path}/repositories (auto-paginating)
    def repositories(self, *, q: str | None = None, sort: str | None = None) -> Iterator[RepositoryPermission]:
        return paginate(lambda cursor: self.repositories_page(q=q, sort=sort, cursor=cursor))

    # GET {path}/repositories
    def repositories_page(
        self,
        *,
        q: str | None = None,
        sort: str | None = None,
        cursor: str | None = None,
    ) -> Page[RepositoryPermission]:
        return self._repository_permissions_page(f"{self._path}/repositories", q=q, sort=sort, cursor=cursor)

    # GET {path}/repositories/{repo_slug} (auto-paginating)
    def repository(
        self,
        repo_slug: str,
        *,
        q: str | None = None,
        sort: str | None = None,
    ) -> Iterator[RepositoryPermission]:
        return paginate(lambda cursor: self.repository_page(repo_slug, q=q, sort=sort, cursor=cursor))

    # GET {path}/repositories/{repo_slug}
    def repository_page(
        self,
        repo_slug: str,
        *,
        q: str | None = None,
        sort: str | None = None,
        cursor: str | None = None,
    ) -> Page[RepositoryPermission]:
        return self._repository_permissions_page(
            f"{self._path}/repositories/{repo_slug}", q=q, sort=sort, cursor=cursor
        )

    def _repository_permissions_page(
        self,
        path: str,
        *,
        q: str | None,
        sort: str | None,
        cursor: str | None,
    ) -> Page[RepositoryPermission]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", path, kind=CqsKind.QUERY, params={"q": q, "sort": sort})
        return page_from_payload(cast("dict[str, Any]", data), RepositoryPermission)
