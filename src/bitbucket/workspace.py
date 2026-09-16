from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.ids import RepositorySlug
from bitbucket.models.pull_request import PullRequest
from bitbucket.repository import RepositoryClient
from bitbucket.resources.base import page_from_payload
from bitbucket.resources.repositories import RepositoriesResource
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport
    from bitbucket.ids import WorkspaceSlug
    from bitbucket.models.pull_request import PullRequestState


class WorkspaceClient:
    def __init__(self, transport: Transport, slug: WorkspaceSlug) -> None:
        self.slug = slug
        self._transport = transport
        self.repositories = RepositoriesResource(transport, slug)

    def repository(self, slug: RepositorySlug | str) -> RepositoryClient:
        return RepositoryClient(self._transport, self.slug, RepositorySlug(str(slug)))

    # GET .../workspaces/{workspace}/pullrequests/{user} (auto-paginating)
    def pull_requests_by_author(
        self,
        user: str,
        *,
        states: list[PullRequestState] | None = None,
        fields: str | None = None,
    ) -> Iterator[PullRequest]:
        # Returns PRs *authored* by `user`. Replacement for
        # /2.0/pullrequests/{user} (removed 2025-02-20); the workspace-scoped
        # route ignores the old `role` parameter.
        return paginate(
            lambda cursor: self._pull_requests_by_author_page(user, states=states, fields=fields, cursor=cursor)
        )

    def _pull_requests_by_author_page(
        self,
        user: str,
        *,
        states: list[PullRequestState] | None,
        fields: str | None,
        cursor: str | None,
    ) -> Page[PullRequest]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            params: dict[str, Any] = {"state": states, "fields": fields}
            path = f"/workspaces/{self.slug}/pullrequests/{user}"
            data = self._transport.request("GET", path, kind=CqsKind.QUERY, params=params)
        return page_from_payload(cast("dict[str, Any]", data), PullRequest)
