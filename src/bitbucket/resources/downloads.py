from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.download import Download
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport


class DownloadsResource:
    # No {id}-keyed create/get pairing NestedResource expects: `create` is a
    # multipart upload, and the item path is keyed by filename, not a server-
    # assigned id — hand-written per the over-abstraction guard in
    # docs/TECH_SPEC.md.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/downloads"

    # DELETE {path}/{filename}
    def delete(self, filename: str) -> None:
        self._transport.request("DELETE", f"{self._path}/{filename}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET {path}/{filename}
    def get(self, filename: str) -> bytes:
        return self._transport.request_bytes("GET", f"{self._path}/{filename}", kind=CqsKind.QUERY)

    # GET {path} (auto-paginating)
    def list(self) -> Iterator[Download]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[Download]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), Download)

    # POST {path}
    def upload(self, filename: str, content: bytes) -> None:
        files = {"files": (filename, content, "application/octet-stream")}
        self._transport.request_multipart("POST", self._path, kind=CqsKind.NON_IDEMPOTENT_COMMAND, files=files)
