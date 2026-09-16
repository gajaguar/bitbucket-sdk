from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.branch import Branch
from bitbucket.models.branch import BranchCreate
from bitbucket.models.ref import Ref
from bitbucket.models.tag import Tag
from bitbucket.models.tag import TagCreate
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport


class BranchesResource:
    # No `update`: Bitbucket has no PUT-by-name endpoint for branches
    # (renaming/retargeting isn't exposed) — hand-written rather than
    # NestedResource so this resource never offers a verb Bitbucket doesn't
    # support, per §3.3's naming contract in docs/TECH_SPEC.md.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/refs/branches"

    # POST {path}
    def create(self, payload: BranchCreate) -> Branch:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request("POST", self._path, kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body)
        return Branch.model_validate(data)

    # DELETE {path}/{name}
    def delete(self, name: str) -> None:
        self._transport.request("DELETE", f"{self._path}/{name}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET {path}/{name}
    def get(self, name: str) -> Branch:
        data = self._transport.request("GET", f"{self._path}/{name}", kind=CqsKind.QUERY)
        return Branch.model_validate(data)

    # GET {path} (auto-paginating)
    def list(self) -> Iterator[Branch]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[Branch]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), Branch)


class TagsResource:
    # No `update`, for the same reason as BranchesResource: tags are
    # immutable once created.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/refs/tags"

    # POST {path}
    def create(self, payload: TagCreate) -> Tag:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request("POST", self._path, kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body)
        return Tag.model_validate(data)

    # DELETE {path}/{name}
    def delete(self, name: str) -> None:
        self._transport.request("DELETE", f"{self._path}/{name}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET {path}/{name}
    def get(self, name: str) -> Tag:
        data = self._transport.request("GET", f"{self._path}/{name}", kind=CqsKind.QUERY)
        return Tag.model_validate(data)

    # GET {path} (auto-paginating)
    def list(self) -> Iterator[Tag]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[Tag]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), Tag)


class RefsResource:
    # Read-only, combined branches+tags listing — hand-written per the
    # over-abstraction guard in docs/TECH_SPEC.md; branches and tags are
    # individually reachable via `.branches`/`.tags`.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/refs"
        self.branches = BranchesResource(transport, base_path)
        self.tags = TagsResource(transport, base_path)

    # GET .../refs (auto-paginating)
    def list(self) -> Iterator[Ref]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET .../refs
    def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[Ref]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), Ref)
