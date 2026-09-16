from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.account import DefaultReviewer
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport
    from bitbucket.ids import RepositorySlug
    from bitbucket.ids import WorkspaceSlug


class DefaultReviewersResource:
    # Read-only, repo-level, with no {id} item path (reviewers are added/removed by
    # PUT/DELETE .../default-reviewers/{account_id}, not modeled here yet) —
    # hand-written per the over-abstraction guard in docs/TECH_SPEC.md.
    def __init__(self, transport: Transport, workspace: WorkspaceSlug, repository: RepositorySlug) -> None:
        self._transport = transport
        self._path = f"/repositories/{workspace}/{repository}/default-reviewers"

    # GET {path} (auto-paginating)
    def list(self) -> Iterator[DefaultReviewer]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[DefaultReviewer]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), DefaultReviewer)
