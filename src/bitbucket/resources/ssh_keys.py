from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.ssh_key import SshKey
from bitbucket.models.ssh_key import SshKeyCreate
from bitbucket.models.ssh_key import SshKeyUpdate
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport


class SshKeysResource:
    # Hand-written: `create` takes an `expires_on` query parameter that
    # NestedResource.create has no way to send.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/ssh-keys"

    # POST {path}
    def create(self, payload: SshKeyCreate, *, expires_on: str | None = None) -> SshKey:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request(
            "POST",
            self._path,
            kind=CqsKind.NON_IDEMPOTENT_COMMAND,
            json=body,
            params={"expires_on": expires_on},
        )
        return SshKey.model_validate(data)

    # GET {path}/{key_id}
    def get(self, key_id: str) -> SshKey:
        data = self._transport.request("GET", f"{self._path}/{key_id}", kind=CqsKind.QUERY)
        return SshKey.model_validate(data)

    # PUT {path}/{key_id}
    def update(self, key_id: str, payload: SshKeyUpdate) -> SshKey:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request("PUT", f"{self._path}/{key_id}", kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
        return SshKey.model_validate(data)

    # DELETE {path}/{key_id}
    def delete(self, key_id: str) -> None:
        self._transport.request("DELETE", f"{self._path}/{key_id}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET {path} (auto-paginating)
    def list(self) -> Iterator[SshKey]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    def list_page(self, *, cursor: str | None = None) -> Page[SshKey]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", self._path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), SshKey)
