from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.models.source import FileHistoryEntry
from bitbucket.models.source import TreeEntry
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from collections.abc import Mapping
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport
    from bitbucket.ids import CommitHash


class AsyncSourceResource:
    # None of these fit AsyncNestedResource's {path}/{id} shape: `GET .../src` is a
    # directory listing at the default branch, `GET .../src/{commit}/{path}`
    # is polymorphic (directory listing or raw file content, disambiguated
    # here by which method the caller picks), `POST .../src` is a multipart
    # commit, and filehistory has its own path shape entirely — hand-written
    # per the over-abstraction guard in docs/TECH_SPEC.md.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._base_path = base_path

    # POST .../src
    async def create_commit(
        self,
        files: Mapping[str, bytes],
        *,
        message: str | None = None,
        branch: str | None = None,
        author: str | None = None,
    ) -> None:
        form_files = {path: (path, content, "application/octet-stream") for path, content in files.items()}
        data = {
            key: value
            for key, value in {"message": message, "branch": branch, "author": author}.items()
            if value is not None
        }
        await self._transport.request_multipart(
            "POST", f"{self._base_path}/src", kind=CqsKind.NON_IDEMPOTENT_COMMAND, files=form_files, data=data
        )

    # GET .../filehistory/{commit}/{path} (auto-paginating)
    def file_history(self, commit: CommitHash | str, path: str) -> AsyncIterator[FileHistoryEntry]:
        return apaginate(lambda cursor: self.file_history_page(commit, path, cursor=cursor))

    # GET .../filehistory/{commit}/{path}
    async def file_history_page(
        self, commit: CommitHash | str, path: str, *, cursor: str | None = None
    ) -> Page[FileHistoryEntry]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            request_path = f"{self._base_path}/filehistory/{commit}/{path}"
            data = await self._transport.request("GET", request_path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), FileHistoryEntry)

    # GET .../src (auto-paginating) — directory listing at the default branch's root
    def list(self) -> AsyncIterator[TreeEntry]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor))

    # GET .../src
    async def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[TreeEntry]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._base_path}/src"
            data = await self._transport.request("GET", path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), TreeEntry)

    # GET .../src/{commit}/{path} (auto-paginating) — directory listing at a path
    def list_path(self, commit: CommitHash | str, path: str = "") -> AsyncIterator[TreeEntry]:
        return apaginate(lambda cursor: self.list_path_page(commit, path, cursor=cursor))

    # GET .../src/{commit}/{path} — directory listing at a path
    async def list_path_page(
        self, commit: CommitHash | str, path: str, *, cursor: str | None = None
    ) -> Page[TreeEntry]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            request_path = f"{self._base_path}/src/{commit}/{path}"
            data = await self._transport.request("GET", request_path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), TreeEntry)

    # GET .../src/{commit}/{path} — raw file content
    async def read(self, commit: CommitHash | str, path: str) -> bytes:
        request_path = f"{self._base_path}/src/{commit}/{path}"
        return await self._transport.request_bytes("GET", request_path, kind=CqsKind.QUERY)
