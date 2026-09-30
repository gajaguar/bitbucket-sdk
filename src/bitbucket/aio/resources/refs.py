from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.models.branch import Branch
from bitbucket.models.branch import BranchCreate
from bitbucket.models.ref import Ref
from bitbucket.models.tag import Tag
from bitbucket.models.tag import TagCreate
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport


class AsyncBranchesResource:
    # No `update`: Bitbucket has no PUT-by-name endpoint for branches
    # (renaming/retargeting isn't exposed) — hand-written rather than
    # AsyncNestedResource so this resource never offers a verb Bitbucket doesn't
    # support, per §3.3's naming contract in docs/TECH_SPEC.md.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/refs/branches"

    # POST {path}
    async def create(self, payload: BranchCreate) -> Branch:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request("POST", self._path, kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body)
        return Branch.model_validate(data)

    # DELETE {path}/{name}
    async def delete(self, name: str) -> None:
        await self._transport.request("DELETE", f"{self._path}/{name}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET {path}/{name}
    async def get(self, name: str) -> Branch:
        data = await self._transport.request("GET", f"{self._path}/{name}", kind=CqsKind.QUERY)
        return Branch.model_validate(data)

    # GET {path} (auto-paginating)
    def list(self) -> AsyncIterator[Branch]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    async def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[Branch]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), Branch)


class AsyncTagsResource:
    # No `update`, for the same reason as AsyncBranchesResource: tags are
    # immutable once created.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/refs/tags"

    # POST {path}
    async def create(self, payload: TagCreate) -> Tag:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request("POST", self._path, kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body)
        return Tag.model_validate(data)

    # DELETE {path}/{name}
    async def delete(self, name: str) -> None:
        await self._transport.request("DELETE", f"{self._path}/{name}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET {path}/{name}
    async def get(self, name: str) -> Tag:
        data = await self._transport.request("GET", f"{self._path}/{name}", kind=CqsKind.QUERY)
        return Tag.model_validate(data)

    # GET {path} (auto-paginating)
    def list(self) -> AsyncIterator[Tag]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    async def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[Tag]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), Tag)


class AsyncRefsResource:
    # Read-only, combined branches+tags listing — hand-written per the
    # over-abstraction guard in docs/TECH_SPEC.md; branches and tags are
    # individually reachable via `.branches`/`.tags`.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/refs"
        self.branches = AsyncBranchesResource(transport, base_path)
        self.tags = AsyncTagsResource(transport, base_path)

    # GET .../refs (auto-paginating)
    def list(self) -> AsyncIterator[Ref]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor))

    # GET .../refs
    async def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[Ref]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), Ref)
