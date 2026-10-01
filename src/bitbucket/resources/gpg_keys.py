from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.gpg_key import GpgKey
from bitbucket.models.gpg_key import GpgKeyCreate
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport


class GpgKeysResource:
    # No `update`: Bitbucket has no PUT for GPG keys, and a key is addressed by
    # its fingerprint rather than an id, so this is not a NestedResource.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/gpg-keys"

    # POST {path}
    def create(self, payload: GpgKeyCreate) -> GpgKey:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request("POST", self._path, kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body)
        return GpgKey.model_validate(data)

    # GET {path}/{fingerprint}
    def get(self, fingerprint: str) -> GpgKey:
        data = self._transport.request("GET", f"{self._path}/{fingerprint}", kind=CqsKind.QUERY)
        return GpgKey.model_validate(data)

    # DELETE {path}/{fingerprint}
    def delete(self, fingerprint: str) -> None:
        self._transport.request("DELETE", f"{self._path}/{fingerprint}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET {path} (auto-paginating)
    def list(self) -> Iterator[GpgKey]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    def list_page(self, *, cursor: str | None = None) -> Page[GpgKey]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", self._path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), GpgKey)
