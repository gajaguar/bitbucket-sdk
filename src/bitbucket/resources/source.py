from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.source import FileHistoryEntry
from bitbucket.models.source import TreeEntry
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from collections.abc import Mapping
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport
    from bitbucket.ids import CommitHash


class SourceResource:
    # None of these fit NestedResource's {path}/{id} shape: `GET .../src` is a
    # directory listing at the default branch, `GET .../src/{commit}/{path}`
    # is polymorphic (directory listing or raw file content, disambiguated
    # here by which method the caller picks), `POST .../src` is a multipart
    # commit, and filehistory has its own path shape entirely — hand-written
    # per the over-abstraction guard in docs/TECH_SPEC.md.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._base_path = base_path

    # POST .../src
    def create_commit(
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
        self._transport.request_multipart(
            "POST", f"{self._base_path}/src", kind=CqsKind.NON_IDEMPOTENT_COMMAND, files=form_files, data=data
        )

    # GET .../filehistory/{commit}/{path} (auto-paginating)
    def file_history(self, commit: CommitHash | str, path: str) -> Iterator[FileHistoryEntry]:
        return paginate(lambda cursor: self._file_history_page(commit, path, cursor=cursor))

    def _file_history_page(self, commit: CommitHash | str, path: str, *, cursor: str | None) -> Page[FileHistoryEntry]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            request_path = f"{self._base_path}/filehistory/{commit}/{path}"
            data = self._transport.request("GET", request_path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), FileHistoryEntry)

    # GET .../src (auto-paginating) — directory listing at the default branch's root
    def list(self) -> Iterator[TreeEntry]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET .../src
    def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[TreeEntry]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            path = f"{self._base_path}/src"
            data = self._transport.request("GET", path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), TreeEntry)

    # GET .../src/{commit}/{path} (auto-paginating) — directory listing at a path
    def list_path(self, commit: CommitHash | str, path: str = "") -> Iterator[TreeEntry]:
        return paginate(lambda cursor: self._list_path_page(commit, path, cursor=cursor))

    def _list_path_page(self, commit: CommitHash | str, path: str, *, cursor: str | None) -> Page[TreeEntry]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            request_path = f"{self._base_path}/src/{commit}/{path}"
            data = self._transport.request("GET", request_path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), TreeEntry)

    # GET .../src/{commit}/{path} — raw file content
    def read(self, commit: CommitHash | str, path: str) -> bytes:
        request_path = f"{self._base_path}/src/{commit}/{path}"
        return self._transport.request_bytes("GET", request_path, kind=CqsKind.QUERY)
