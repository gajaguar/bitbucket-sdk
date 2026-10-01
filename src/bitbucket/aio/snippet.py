from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.aio.resources.snippets import AsyncSnippetCommentsResource
from bitbucket.aio.resources.snippets import update_snippet
from bitbucket.errors import NotFoundError
from bitbucket.models.account import Account
from bitbucket.models.snippet import Snippet
from bitbucket.models.snippet import SnippetCommit
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from collections.abc import Mapping
    from collections.abc import Sequence
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport
    from bitbucket.ids import WorkspaceSlug
    from bitbucket.models.snippet import SnippetUpdate


class AsyncSnippetClient:
    # Async mirror of SnippetClient.
    def __init__(self, transport: AsyncTransport, workspace: WorkspaceSlug, snippet_id: str) -> None:
        self.snippet_id = snippet_id
        self._transport = transport
        self._path = f"/snippets/{workspace}/{snippet_id}"
        self.comments = AsyncSnippetCommentsResource(transport, self._path)

    # GET .../snippets/{workspace}/{encoded_id}/commits/{revision}
    async def commit(self, revision: str) -> SnippetCommit:
        data = await self._transport.request("GET", f"{self._path}/commits/{revision}", kind=CqsKind.QUERY)
        return SnippetCommit.model_validate(data)

    # GET .../snippets/{workspace}/{encoded_id}/commits (auto-paginating)
    def commits(self) -> AsyncIterator[SnippetCommit]:
        return apaginate(lambda cursor: self.commits_page(cursor=cursor))

    # GET .../snippets/{workspace}/{encoded_id}/commits
    async def commits_page(self, *, cursor: str | None = None) -> Page[SnippetCommit]:
        data = await self._transport.request("GET", cursor or f"{self._path}/commits", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), SnippetCommit)

    # GET .../snippets/{workspace}/{encoded_id}/{revision}/diff
    async def diff(self, revision: str, *, path: str | None = None) -> str:
        return await self._transport.request_text(
            "GET", f"{self._path}/{revision}/diff", kind=CqsKind.QUERY, params={"path": path}
        )

    # GET .../snippets/{workspace}/{encoded_id}/files/{path}
    async def file(self, path: str) -> bytes:
        return await self._transport.request_bytes(
            "GET", f"{self._path}/files/{path}", kind=CqsKind.QUERY, follow_redirects=True
        )

    # GET .../snippets/{workspace}/{encoded_id}/watch
    async def is_watching(self) -> bool:
        try:
            await self._transport.request("GET", f"{self._path}/watch", kind=CqsKind.QUERY)
        except NotFoundError:
            return False
        return True

    # DELETE .../snippets/{workspace}/{encoded_id}/watch
    async def unwatch(self) -> None:
        await self._transport.request("DELETE", f"{self._path}/watch", kind=CqsKind.IDEMPOTENT_COMMAND)

    # PUT .../snippets/{workspace}/{encoded_id}/watch
    async def watch(self) -> None:
        await self._transport.request("PUT", f"{self._path}/watch", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET .../snippets/{workspace}/{encoded_id}/{revision}/patch
    async def patch(self, revision: str) -> str:
        return await self._transport.request_text("GET", f"{self._path}/{revision}/patch", kind=CqsKind.QUERY)

    def revision(self, node_id: str) -> AsyncSnippetRevision:
        return AsyncSnippetRevision(self._transport, self._path, node_id)

    # GET .../snippets/{workspace}/{encoded_id}/watchers (auto-paginating)
    def watchers(self) -> AsyncIterator[Account]:
        return apaginate(lambda cursor: self.watchers_page(cursor=cursor))

    # GET .../snippets/{workspace}/{encoded_id}/watchers
    async def watchers_page(self, *, cursor: str | None = None) -> Page[Account]:
        data = await self._transport.request("GET", cursor or f"{self._path}/watchers", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Account)


class AsyncSnippetRevision:
    # Async mirror of SnippetRevision.
    def __init__(self, transport: AsyncTransport, snippet_path: str, node_id: str) -> None:
        self.node_id = node_id
        self._transport = transport
        self._path = f"{snippet_path}/{node_id}"

    # DELETE .../snippets/{workspace}/{encoded_id}/{node_id}
    async def delete(self) -> None:
        await self._transport.request("DELETE", self._path, kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET .../snippets/{workspace}/{encoded_id}/{node_id}/files/{path}
    async def file(self, path: str) -> bytes:
        return await self._transport.request_bytes("GET", f"{self._path}/files/{path}", kind=CqsKind.QUERY)

    # GET .../snippets/{workspace}/{encoded_id}/{node_id}
    async def get(self) -> Snippet:
        data = await self._transport.request("GET", self._path, kind=CqsKind.QUERY)
        return Snippet.model_validate(data)

    # PUT .../snippets/{workspace}/{encoded_id}/{node_id}
    async def update(
        self,
        payload: SnippetUpdate,
        *,
        files: Mapping[str, bytes] | None = None,
        delete_files: Sequence[str] = (),
    ) -> Snippet:
        return await update_snippet(self._transport, self._path, payload, files, delete_files)
