from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.aio.project import AsyncProjectClient
from bitbucket.aio.repository import AsyncRepositoryClient
from bitbucket.aio.resources.hooks import AsyncHooksResource
from bitbucket.aio.resources.repositories import AsyncRepositoriesResource
from bitbucket.ids import ProjectKey
from bitbucket.ids import RepositorySlug
from bitbucket.models.pull_request import PullRequest
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

    def repository(self, slug: RepositorySlug | str) -> AsyncRepositoryClient:
        return AsyncRepositoryClient(self._transport, self.slug, RepositorySlug(str(slug)))

    def project(self, key: ProjectKey | str) -> AsyncProjectClient:
        return AsyncProjectClient(self._transport, self.slug, ProjectKey(str(key)))

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
