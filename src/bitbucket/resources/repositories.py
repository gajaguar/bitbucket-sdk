from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.activity import Activity
from bitbucket.models.pull_request import PullRequest
from bitbucket.models.repository import Repository
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport
    from bitbucket.ids import CommitHash
    from bitbucket.ids import RepositorySlug
    from bitbucket.ids import WorkspaceSlug


class RepositoriesResource:
    # Read-only and workspace-scoped (no per-repo {id} nesting a create/update/delete
    # would hang off), unlike pull requests and comments — hand-written rather than
    # NestedResource, per the over-abstraction guard in docs/TECH_SPEC.md.
    def __init__(self, transport: Transport, workspace: WorkspaceSlug) -> None:
        self._transport = transport
        self._workspace = workspace

    # GET .../repositories/{workspace}/{repo_slug}
    def get(self, slug: RepositorySlug | str) -> Repository:
        data = self._transport.request("GET", self._item_path(slug), kind=CqsKind.QUERY)
        return Repository.model_validate(data)

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
