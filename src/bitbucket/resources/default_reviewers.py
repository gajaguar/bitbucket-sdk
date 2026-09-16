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
    # {id} item path uses {target_username}, not {account_id} — see the note in
    # docs/coverage.md — and has no create/update body, so it doesn't fit
    # NestedResource's {path}/{id} shape — hand-written per the
    # over-abstraction guard in docs/TECH_SPEC.md.
    def __init__(self, transport: Transport, workspace: WorkspaceSlug, repository: RepositorySlug) -> None:
        self._transport = transport
        self._base_path = f"/repositories/{workspace}/{repository}"
        self._path = f"{self._base_path}/default-reviewers"

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

    # GET {path}/{target_username}
    def get(self, target_username: str) -> DefaultReviewer:
        data = self._transport.request("GET", f"{self._path}/{target_username}", kind=CqsKind.QUERY)
        return DefaultReviewer.model_validate(data)

    # PUT {path}/{target_username}
    def add(self, target_username: str) -> DefaultReviewer:
        data = self._transport.request("PUT", f"{self._path}/{target_username}", kind=CqsKind.IDEMPOTENT_COMMAND)
        return DefaultReviewer.model_validate(data)

    # DELETE {path}/{target_username}
    def remove(self, target_username: str) -> None:
        self._transport.request("DELETE", f"{self._path}/{target_username}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET .../effective-default-reviewers (auto-paginating)
    def effective(self) -> Iterator[DefaultReviewer]:
        return paginate(lambda cursor: self.effective_page(cursor=cursor))

    # GET .../effective-default-reviewers
    def effective_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[DefaultReviewer]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._base_path}/effective-default-reviewers"
            data = self._transport.request("GET", path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), DefaultReviewer)
