from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.errors import NotFoundError
from bitbucket.models.account import Account
from bitbucket.resources.base import page_from_payload
from bitbucket.resources.snippets import SnippetCommentsResource
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport
    from bitbucket.ids import WorkspaceSlug


class SnippetClient:
    # A thin wiring class like RepositoryClient, for /snippets/{workspace}/{encoded_id};
    # it sends no request until a method is called.
    def __init__(self, transport: Transport, workspace: WorkspaceSlug, snippet_id: str) -> None:
        self.snippet_id = snippet_id
        self._transport = transport
        self._path = f"/snippets/{workspace}/{snippet_id}"
        self.comments = SnippetCommentsResource(transport, self._path)

    # GET .../snippets/{workspace}/{encoded_id}/watch
    def is_watching(self) -> bool:
        # The spec answers 404 both when the user is not watching and when the
        # snippet does not exist, so a missing snippet also reads as False.
        try:
            self._transport.request("GET", f"{self._path}/watch", kind=CqsKind.QUERY)
        except NotFoundError:
            return False
        return True

    # DELETE .../snippets/{workspace}/{encoded_id}/watch
    def unwatch(self) -> None:
        self._transport.request("DELETE", f"{self._path}/watch", kind=CqsKind.IDEMPOTENT_COMMAND)

    # PUT .../snippets/{workspace}/{encoded_id}/watch
    def watch(self) -> None:
        self._transport.request("PUT", f"{self._path}/watch", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET .../snippets/{workspace}/{encoded_id}/watchers (auto-paginating)
    def watchers(self) -> Iterator[Account]:
        return paginate(lambda cursor: self._watchers_page(cursor=cursor))

    def _watchers_page(self, *, cursor: str | None) -> Page[Account]:
        data = self._transport.request("GET", cursor or f"{self._path}/watchers", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Account)
