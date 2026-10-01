from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.aio.resources.snippets import AsyncSnippetCommentsResource
from bitbucket.errors import NotFoundError
from bitbucket.models.account import Account
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport
    from bitbucket.ids import WorkspaceSlug


class AsyncSnippetClient:
    # Async mirror of SnippetClient.
    def __init__(self, transport: AsyncTransport, workspace: WorkspaceSlug, snippet_id: str) -> None:
        self.snippet_id = snippet_id
        self._transport = transport
        self._path = f"/snippets/{workspace}/{snippet_id}"
        self.comments = AsyncSnippetCommentsResource(transport, self._path)

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

    # GET .../snippets/{workspace}/{encoded_id}/watchers (auto-paginating)
    def watchers(self) -> AsyncIterator[Account]:
        return apaginate(lambda cursor: self._watchers_page(cursor=cursor))

    async def _watchers_page(self, *, cursor: str | None) -> Page[Account]:
        data = await self._transport.request("GET", cursor or f"{self._path}/watchers", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Account)
