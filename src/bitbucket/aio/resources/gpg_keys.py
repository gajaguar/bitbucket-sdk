from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.models.gpg_key import GpgKey
from bitbucket.models.gpg_key import GpgKeyCreate
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport


class AsyncGpgKeysResource:
    # No `update`: Bitbucket has no PUT for GPG keys, and a key is addressed by
    # its fingerprint rather than an id, so this is not a NestedResource.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/gpg-keys"

    # POST {path}
    async def create(self, payload: GpgKeyCreate) -> GpgKey:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request("POST", self._path, kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body)
        return GpgKey.model_validate(data)

    # GET {path}/{fingerprint}
    async def get(self, fingerprint: str) -> GpgKey:
        data = await self._transport.request("GET", f"{self._path}/{fingerprint}", kind=CqsKind.QUERY)
        return GpgKey.model_validate(data)

    # DELETE {path}/{fingerprint}
    async def delete(self, fingerprint: str) -> None:
        await self._transport.request("DELETE", f"{self._path}/{fingerprint}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET {path} (auto-paginating)
    def list(self) -> AsyncIterator[GpgKey]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    async def list_page(self, *, cursor: str | None = None) -> Page[GpgKey]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request("GET", self._path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), GpgKey)
