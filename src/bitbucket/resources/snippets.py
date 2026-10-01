from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.comment import CommentUpdate
from bitbucket.models.snippet import Snippet
from bitbucket.models.snippet import SnippetComment
from bitbucket.models.snippet import SnippetCommentCreate
from bitbucket.resources.base import DeletableResourceMixin
from bitbucket.resources.base import NestedResource
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from collections.abc import Mapping
    from collections.abc import Sequence
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import MultipartPart
    from bitbucket._transport import Transport
    from bitbucket.models.base import BitbucketModel
    from bitbucket.models.snippet import SnippetCreate
    from bitbucket.models.snippet import SnippetRole
    from bitbucket.models.snippet import SnippetUpdate

_BINARY: Final = "application/octet-stream"


def _form_text(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def form_parts(
    payload: BitbucketModel,
    files: Mapping[str, bytes] | None,
    delete_files: Sequence[str],
) -> list[tuple[str, MultipartPart]]:
    # The spec's multipart/form-data mode: metadata as flat form fields, one repeated
    # `file` part per file, and a repeated `files` field naming each file to delete.
    # A form field cannot carry `null`, so an unset or None field is left out.
    fields = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
    parts: list[tuple[str, MultipartPart]] = [
        (name, (None, _form_text(value), None)) for name, value in fields.items()
    ]
    parts.extend(("files", (None, name, None)) for name in delete_files)
    parts.extend(("file", (name, content, _BINARY)) for name, content in (files or {}).items())
    return parts


class UserSnippetsResource:
    # POST /snippets, the one operation outside a workspace: it creates the snippet
    # under the authenticated user's account.
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    # POST /snippets
    def create(self, payload: SnippetCreate, *, files: Mapping[str, bytes] | None = None) -> Snippet:
        parts = form_parts(payload, files, ())
        data = self._transport.request_multipart("POST", "/snippets", kind=CqsKind.NON_IDEMPOTENT_COMMAND, files=parts)
        return Snippet.model_validate(data)


class SnippetsResource:
    # Create and update take file contents, which JSON cannot carry, so neither fits
    # NestedResource's JSON-only create/update — hand-written per the
    # over-abstraction guard in docs/TECH_SPEC.md.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = base_path

    # POST .../snippets/{workspace}
    def create(self, payload: SnippetCreate, *, files: Mapping[str, bytes] | None = None) -> Snippet:
        parts = form_parts(payload, files, ())
        data = self._transport.request_multipart("POST", self._path, kind=CqsKind.NON_IDEMPOTENT_COMMAND, files=parts)
        return Snippet.model_validate(data)

    # DELETE .../snippets/{workspace}/{encoded_id}
    def delete(self, snippet_id: str) -> None:
        self._transport.request("DELETE", f"{self._path}/{snippet_id}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET .../snippets/{workspace}/{encoded_id}
    def get(self, snippet_id: str) -> Snippet:
        data = self._transport.request("GET", f"{self._path}/{snippet_id}", kind=CqsKind.QUERY)
        return Snippet.model_validate(data)

    # GET .../snippets/{workspace} (auto-paginating)
    def list(self, *, role: SnippetRole | None = None) -> Iterator[Snippet]:
        return paginate(lambda cursor: self.list_page(cursor=cursor, role=role))

    # GET .../snippets/{workspace}
    def list_page(self, *, cursor: str | None = None, role: SnippetRole | None = None) -> Page[Snippet]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request(
                "GET", self._path, kind=CqsKind.QUERY, params={"role": role.value if role else None}
            )
        return page_from_payload(cast("dict[str, Any]", data), Snippet)

    # PUT .../snippets/{workspace}/{encoded_id}
    def update(
        self,
        snippet_id: str,
        payload: SnippetUpdate,
        *,
        files: Mapping[str, bytes] | None = None,
        delete_files: Sequence[str] = (),
    ) -> Snippet:
        return update_snippet(self._transport, f"{self._path}/{snippet_id}", payload, files, delete_files)


def update_snippet(
    transport: Transport,
    path: str,
    payload: SnippetUpdate,
    files: Mapping[str, bytes] | None,
    delete_files: Sequence[str],
) -> Snippet:
    # JSON carries metadata only; file changes need multipart/form-data. A JSON body
    # keeps `null`, which the spec uses to delete a property such as the title.
    if files or delete_files:
        parts = form_parts(payload, files, delete_files)
        data = transport.request_multipart("PUT", path, kind=CqsKind.IDEMPOTENT_COMMAND, files=parts)
    else:
        body = payload.model_dump(mode="json", exclude_unset=True)
        data = transport.request("PUT", path, kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
    return Snippet.model_validate(data)


class SnippetCommentsResource(
    NestedResource[SnippetComment, SnippetCommentCreate, CommentUpdate],
    DeletableResourceMixin,
):
    _path = "/comments"
    _read_model = SnippetComment
