from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.aio.resources.base import AsyncDeletableResourceMixin
from bitbucket.aio.resources.base import AsyncNestedResource
from bitbucket.models.comment import CommentUpdate
from bitbucket.models.snippet import Snippet
from bitbucket.models.snippet import SnippetComment
from bitbucket.models.snippet import SnippetCommentCreate
from bitbucket.resources.base import page_from_payload
from bitbucket.resources.snippets import form_parts
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from collections.abc import Mapping
    from collections.abc import Sequence
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport
    from bitbucket.models.snippet import SnippetCreate
    from bitbucket.models.snippet import SnippetRole
    from bitbucket.models.snippet import SnippetUpdate


class AsyncUserSnippetsResource:
    # Async mirror of UserSnippetsResource.
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    # POST /snippets
    async def create(self, payload: SnippetCreate, *, files: Mapping[str, bytes] | None = None) -> Snippet:
        parts = form_parts(payload, files, ())
        data = await self._transport.request_multipart(
            "POST", "/snippets", kind=CqsKind.NON_IDEMPOTENT_COMMAND, files=parts
        )
        return Snippet.model_validate(data)


class AsyncSnippetsResource:
    # Async mirror of SnippetsResource.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._path = base_path

    # POST .../snippets/{workspace}
    async def create(self, payload: SnippetCreate, *, files: Mapping[str, bytes] | None = None) -> Snippet:
        parts = form_parts(payload, files, ())
        data = await self._transport.request_multipart(
            "POST", self._path, kind=CqsKind.NON_IDEMPOTENT_COMMAND, files=parts
        )
        return Snippet.model_validate(data)

    # DELETE .../snippets/{workspace}/{encoded_id}
    async def delete(self, snippet_id: str) -> None:
        await self._transport.request("DELETE", f"{self._path}/{snippet_id}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET .../snippets/{workspace}/{encoded_id}
    async def get(self, snippet_id: str) -> Snippet:
        data = await self._transport.request("GET", f"{self._path}/{snippet_id}", kind=CqsKind.QUERY)
        return Snippet.model_validate(data)

    # GET .../snippets/{workspace} (auto-paginating)
    def list(self, *, role: SnippetRole | None = None) -> AsyncIterator[Snippet]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor, role=role))

    # GET .../snippets/{workspace}
    async def list_page(self, *, cursor: str | None = None, role: SnippetRole | None = None) -> Page[Snippet]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request(
                "GET", self._path, kind=CqsKind.QUERY, params={"role": role.value if role else None}
            )
        return page_from_payload(cast("dict[str, Any]", data), Snippet)

    # PUT .../snippets/{workspace}/{encoded_id}
    async def update(
        self,
        snippet_id: str,
        payload: SnippetUpdate,
        *,
        files: Mapping[str, bytes] | None = None,
        delete_files: Sequence[str] = (),
    ) -> Snippet:
        return await update_snippet(self._transport, f"{self._path}/{snippet_id}", payload, files, delete_files)


async def update_snippet(
    transport: AsyncTransport,
    path: str,
    payload: SnippetUpdate,
    files: Mapping[str, bytes] | None,
    delete_files: Sequence[str],
) -> Snippet:
    if files or delete_files:
        parts = form_parts(payload, files, delete_files)
        data = await transport.request_multipart("PUT", path, kind=CqsKind.IDEMPOTENT_COMMAND, files=parts)
    else:
        body = payload.model_dump(mode="json", exclude_unset=True)
        data = await transport.request("PUT", path, kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
    return Snippet.model_validate(data)


class AsyncSnippetCommentsResource(
    AsyncNestedResource[SnippetComment, SnippetCommentCreate, CommentUpdate],
    AsyncDeletableResourceMixin,
):
    _path = "/comments"
    _read_model = SnippetComment
