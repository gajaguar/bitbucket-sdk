from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.ids import ProjectKey
from bitbucket.ids import RepositorySlug
from bitbucket.models.permission import RepositoryPermission
from bitbucket.models.pull_request import PullRequest
from bitbucket.models.workspace import Workspace
from bitbucket.models.workspace import WorkspaceMembership
from bitbucket.project import ProjectClient
from bitbucket.repository import RepositoryClient
from bitbucket.resources.base import page_from_payload
from bitbucket.resources.hooks import HooksResource
from bitbucket.resources.pipelines_config import WorkspacePipelinesConfig
from bitbucket.resources.projects import ProjectsResource
from bitbucket.resources.repositories import RepositoriesResource
from bitbucket.resources.search import SearchResource
from bitbucket.resources.workspaces import WorkspaceMembersResource
from bitbucket.resources.workspaces import WorkspacePermissionsResource
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
        self.hooks = HooksResource(transport, f"/workspaces/{slug}")
        self.projects = ProjectsResource(transport, f"/workspaces/{slug}")
        self.members = WorkspaceMembersResource(transport, f"/workspaces/{slug}")
        self.permissions = WorkspacePermissionsResource(transport, f"/workspaces/{slug}")
        self.search = SearchResource(transport, f"/workspaces/{slug}")
        self.pipelines_config = WorkspacePipelinesConfig(transport, f"/workspaces/{slug}")

    def repository(self, slug: RepositorySlug | str) -> RepositoryClient:
        return RepositoryClient(self._transport, self.slug, RepositorySlug(str(slug)))

    def project(self, key: ProjectKey | str) -> ProjectClient:
        return ProjectClient(self._transport, self.slug, ProjectKey(str(key)))

    # GET .../workspaces/{workspace}
    def get(self) -> Workspace:
        data = self._transport.request("GET", f"/workspaces/{self.slug}", kind=CqsKind.QUERY)
        return Workspace.model_validate(data)

    # GET .../workspaces/{workspace}/settings/gpg/public-key
    def gpg_public_key(self) -> str:
        # Plain text; one key, or two while Bitbucket rotates it.
        path = f"/workspaces/{self.slug}/settings/gpg/public-key"
        return self._transport.request_text("GET", path, kind=CqsKind.QUERY)

    # GET .../user/workspaces/{workspace}/permission
    def my_permission(self) -> WorkspaceMembership:
        data = self._transport.request("GET", f"/user/workspaces/{self.slug}/permission", kind=CqsKind.QUERY)
        return WorkspaceMembership.model_validate(data)

    # GET .../user/workspaces/{workspace}/permissions/repositories (auto-paginating)
    def my_repository_permissions(
        self,
        *,
        q: str | None = None,
        sort: str | None = None,
    ) -> Iterator[RepositoryPermission]:
        return paginate(lambda cursor: self.my_repository_permissions_page(q=q, sort=sort, cursor=cursor))

    # GET .../user/workspaces/{workspace}/permissions/repositories
    def my_repository_permissions_page(
        self,
        *,
        q: str | None = None,
        sort: str | None = None,
        cursor: str | None = None,
    ) -> Page[RepositoryPermission]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"/user/workspaces/{self.slug}/permissions/repositories"
            data = self._transport.request("GET", path, kind=CqsKind.QUERY, params={"q": q, "sort": sort})
        return page_from_payload(cast("dict[str, Any]", data), RepositoryPermission)

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
