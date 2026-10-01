from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.aio.project import AsyncProjectClient
from bitbucket.aio.repository import AsyncRepositoryClient
from bitbucket.aio.resources.hooks import AsyncHooksResource
from bitbucket.aio.resources.pipelines_config import AsyncWorkspacePipelinesConfig
from bitbucket.aio.resources.projects import AsyncProjectsResource
from bitbucket.aio.resources.repositories import AsyncRepositoriesResource
from bitbucket.aio.resources.search import AsyncSearchResource
from bitbucket.aio.resources.snippets import AsyncSnippetsResource
from bitbucket.aio.resources.workspaces import AsyncWorkspaceMembersResource
from bitbucket.aio.resources.workspaces import AsyncWorkspacePermissionsResource
from bitbucket.aio.snippet import AsyncSnippetClient
from bitbucket.ids import ProjectKey
from bitbucket.ids import RepositorySlug
from bitbucket.models.permission import RepositoryPermission
from bitbucket.models.pull_request import PullRequest
from bitbucket.models.workspace import Workspace
from bitbucket.models.workspace import WorkspaceMembership
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport
    from bitbucket.ids import WorkspaceSlug
    from bitbucket.models.pull_request import PullRequestState


class AsyncWorkspaceClient:
    def __init__(self, transport: AsyncTransport, slug: WorkspaceSlug) -> None:
        self.slug = slug
        self._transport = transport
        self.repositories = AsyncRepositoriesResource(transport, slug)
        self.hooks = AsyncHooksResource(transport, f"/workspaces/{slug}")
        self.projects = AsyncProjectsResource(transport, f"/workspaces/{slug}")
        self.members = AsyncWorkspaceMembersResource(transport, f"/workspaces/{slug}")
        self.permissions = AsyncWorkspacePermissionsResource(transport, f"/workspaces/{slug}")
        self.search = AsyncSearchResource(transport, f"/workspaces/{slug}")
        self.pipelines_config = AsyncWorkspacePipelinesConfig(transport, f"/workspaces/{slug}")
        self.snippets = AsyncSnippetsResource(transport, f"/snippets/{slug}")

    def repository(self, slug: RepositorySlug | str) -> AsyncRepositoryClient:
        return AsyncRepositoryClient(self._transport, self.slug, RepositorySlug(str(slug)))

    def snippet(self, snippet_id: str) -> AsyncSnippetClient:
        return AsyncSnippetClient(self._transport, self.slug, snippet_id)

    def project(self, key: ProjectKey | str) -> AsyncProjectClient:
        return AsyncProjectClient(self._transport, self.slug, ProjectKey(str(key)))

    # GET .../workspaces/{workspace}
    async def get(self) -> Workspace:
        data = await self._transport.request("GET", f"/workspaces/{self.slug}", kind=CqsKind.QUERY)
        return Workspace.model_validate(data)

    # GET .../workspaces/{workspace}/settings/gpg/public-key
    async def gpg_public_key(self) -> str:
        # Plain text; one key, or two while Bitbucket rotates it.
        path = f"/workspaces/{self.slug}/settings/gpg/public-key"
        return await self._transport.request_text("GET", path, kind=CqsKind.QUERY)

    # GET .../user/workspaces/{workspace}/permission
    async def my_permission(self) -> WorkspaceMembership:
        data = await self._transport.request("GET", f"/user/workspaces/{self.slug}/permission", kind=CqsKind.QUERY)
        return WorkspaceMembership.model_validate(data)

    # GET .../user/workspaces/{workspace}/permissions/repositories (auto-paginating)
    def my_repository_permissions(
        self,
        *,
        q: str | None = None,
        sort: str | None = None,
    ) -> AsyncIterator[RepositoryPermission]:
        return apaginate(lambda cursor: self.my_repository_permissions_page(q=q, sort=sort, cursor=cursor))

    # GET .../user/workspaces/{workspace}/permissions/repositories
    async def my_repository_permissions_page(
        self,
        *,
        q: str | None = None,
        sort: str | None = None,
        cursor: str | None = None,
    ) -> Page[RepositoryPermission]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"/user/workspaces/{self.slug}/permissions/repositories"
            data = await self._transport.request("GET", path, kind=CqsKind.QUERY, params={"q": q, "sort": sort})
        return page_from_payload(cast("dict[str, Any]", data), RepositoryPermission)

    # GET .../workspaces/{workspace}/pullrequests/{user} (auto-paginating)
    def pull_requests_by_author(
        self,
        user: str,
        *,
        states: list[PullRequestState] | None = None,
        fields: str | None = None,
    ) -> AsyncIterator[PullRequest]:
        # Returns PRs *authored* by `user`. Replacement for
        # /2.0/pullrequests/{user} (removed 2025-02-20); the workspace-scoped
        # route ignores the old `role` parameter.
        return apaginate(
            lambda cursor: self._pull_requests_by_author_page(user, states=states, fields=fields, cursor=cursor)
        )

    async def _pull_requests_by_author_page(
        self,
        user: str,
        *,
        states: list[PullRequestState] | None,
        fields: str | None,
        cursor: str | None,
    ) -> Page[PullRequest]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            params: dict[str, Any] = {"state": states, "fields": fields}
            path = f"/workspaces/{self.slug}/pullrequests/{user}"
            data = await self._transport.request("GET", path, kind=CqsKind.QUERY, params=params)
        return page_from_payload(cast("dict[str, Any]", data), PullRequest)
