from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.account import Account
from bitbucket.models.activity import Activity
from bitbucket.models.pull_request import PullRequest
from bitbucket.models.repository import ForkCreate
from bitbucket.models.repository import Repository
from bitbucket.models.repository import RepositoryCreate
from bitbucket.models.repository import RepositoryUpdate
from bitbucket.resources.base import page_from_payload
from bitbucket.resources.hooks import HooksResource
from bitbucket.resources.permissions import RepositoryPermissionsResource
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport
    from bitbucket.ids import CommitHash
    from bitbucket.ids import RepositorySlug
    from bitbucket.ids import WorkspaceSlug


class RepositoriesResource:
    # Workspace-scoped, with no per-repo {id} nesting a create/update/delete
    # could hang off in NestedResource's shape: create puts the slug in the
    # *path*, not the body (see the note in docs/coverage.md) — hand-written
    # per the over-abstraction guard in docs/TECH_SPEC.md.
    def __init__(self, transport: Transport, workspace: WorkspaceSlug) -> None:
        self._transport = transport
        self._workspace = workspace

    # POST .../repositories/{workspace}/{repo_slug}
    def create(self, slug: RepositorySlug | str, payload: RepositoryCreate) -> Repository:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request("POST", self._item_path(slug), kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body)
        return Repository.model_validate(data)

    # DELETE .../repositories/{workspace}/{repo_slug}
    def delete(self, slug: RepositorySlug | str) -> None:
        self._transport.request("DELETE", self._item_path(slug), kind=CqsKind.IDEMPOTENT_COMMAND)

    # POST .../repositories/{workspace}/{repo_slug}/forks
    def create_fork(self, slug: RepositorySlug | str, payload: ForkCreate | None = None) -> Repository:
        body = (payload or ForkCreate()).model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request(
            "POST", f"{self._item_path(slug)}/forks", kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body
        )
        return Repository.model_validate(data)

    # GET .../repositories/{workspace}/{repo_slug}/forks (auto-paginating)
    def forks(self, slug: RepositorySlug | str) -> Iterator[Repository]:
        return paginate(lambda cursor: self._forks_page(slug, cursor=cursor))

    def _forks_page(self, slug: RepositorySlug | str, *, cursor: str | None) -> Page[Repository]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", f"{self._item_path(slug)}/forks", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Repository)

    # GET .../repositories/{workspace}/{repo_slug}
    def get(self, slug: RepositorySlug | str) -> Repository:
        data = self._transport.request("GET", self._item_path(slug), kind=CqsKind.QUERY)
        return Repository.model_validate(data)

    def hooks(self, slug: RepositorySlug | str) -> HooksResource:
        return HooksResource(self._transport, self._item_path(slug))

    # GET .../repositories/{workspace} (auto-paginating)
    def list(self, *, q: str | None = None, sort: str | None = None) -> Iterator[Repository]:
        return paginate(lambda cursor: self.list_page(cursor=cursor, q=q, sort=sort))

    # GET .../repositories/{workspace}
    def list_page(
        self,
        *,
        cursor: str | None = None,
        q: str | None = None,
        sort: str | None = None,
        pagelen: int = 100,
    ) -> Page[Repository]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            params: dict[str, Any] = {"pagelen": pagelen, "q": q, "sort": sort}
            data = self._transport.request("GET", self._collection_path(), kind=CqsKind.QUERY, params=params)
        return page_from_payload(cast("dict[str, Any]", data), Repository)

    def permissions(self, slug: RepositorySlug | str) -> RepositoryPermissionsResource:
        return RepositoryPermissionsResource(self._transport, self._item_path(slug))

    # PUT .../repositories/{workspace}/{repo_slug}
    def update(self, slug: RepositorySlug | str, payload: RepositoryUpdate) -> Repository:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request("PUT", self._item_path(slug), kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
        return Repository.model_validate(data)

    # GET .../repositories/{workspace}/{repo_slug}/watchers (auto-paginating)
    def watchers(self, slug: RepositorySlug | str) -> Iterator[Account]:
        return paginate(lambda cursor: self._watchers_page(slug, cursor=cursor))

    def _watchers_page(self, slug: RepositorySlug | str, *, cursor: str | None) -> Page[Account]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", f"{self._item_path(slug)}/watchers", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Account)

    # GET .../commit/{commit}/pullrequests (auto-paginating)
    def commit_pull_requests(self, slug: RepositorySlug | str, commit: CommitHash | str) -> Iterator[PullRequest]:
        return paginate(lambda cursor: self._commit_pull_requests_page(slug, commit, cursor=cursor))

    def _commit_pull_requests_page(
        self, slug: RepositorySlug | str, commit: CommitHash | str, *, cursor: str | None
    ) -> Page[PullRequest]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._item_path(slug)}/commit/{commit}/pullrequests"
            data = self._transport.request("GET", path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), PullRequest)

    # GET .../pullrequests/activity (auto-paginating)
    def pull_request_activity(self, slug: RepositorySlug | str) -> Iterator[Activity]:
        return paginate(lambda cursor: self._pull_request_activity_page(slug, cursor=cursor))

    def _pull_request_activity_page(self, slug: RepositorySlug | str, *, cursor: str | None) -> Page[Activity]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._item_path(slug)}/pullrequests/activity"
            data = self._transport.request("GET", path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Activity)

    def _collection_path(self) -> str:
        return f"/repositories/{self._workspace}"

    def _item_path(self, slug: RepositorySlug | str) -> str:
        return f"{self._collection_path()}/{slug}"
