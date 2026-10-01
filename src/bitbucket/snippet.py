from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.errors import NotFoundError
from bitbucket.models.account import Account
from bitbucket.models.snippet import Snippet
from bitbucket.models.snippet import SnippetCommit
from bitbucket.resources.base import page_from_payload
from bitbucket.resources.snippets import SnippetCommentsResource
from bitbucket.resources.snippets import update_snippet
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from collections.abc import Mapping
    from collections.abc import Sequence
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport
    from bitbucket.ids import WorkspaceSlug
    from bitbucket.models.snippet import SnippetUpdate


class SnippetClient:
    # A thin wiring class like RepositoryClient, for /snippets/{workspace}/{encoded_id};
    # it sends no request until a method is called.
    def __init__(self, transport: Transport, workspace: WorkspaceSlug, snippet_id: str) -> None:
        self.snippet_id = snippet_id
        self._transport = transport
        self._path = f"/snippets/{workspace}/{snippet_id}"
        self.comments = SnippetCommentsResource(transport, self._path)

    # GET .../snippets/{workspace}/{encoded_id}/commits/{revision}
    def commit(self, revision: str) -> SnippetCommit:
        data = self._transport.request("GET", f"{self._path}/commits/{revision}", kind=CqsKind.QUERY)
        return SnippetCommit.model_validate(data)

    # GET .../snippets/{workspace}/{encoded_id}/commits (auto-paginating)
    def commits(self) -> Iterator[SnippetCommit]:
        return paginate(lambda cursor: self.commits_page(cursor=cursor))

    # GET .../snippets/{workspace}/{encoded_id}/commits
    def commits_page(self, *, cursor: str | None = None) -> Page[SnippetCommit]:
        data = self._transport.request("GET", cursor or f"{self._path}/commits", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), SnippetCommit)

    # GET .../snippets/{workspace}/{encoded_id}/{revision}/diff
    def diff(self, revision: str, *, path: str | None = None) -> str:
        return self._transport.request_text(
            "GET", f"{self._path}/{revision}/diff", kind=CqsKind.QUERY, params={"path": path}
        )

    # GET .../snippets/{workspace}/{encoded_id}/files/{path}
    def file(self, path: str) -> bytes:
        # Answers 302 to the file at the latest revision, so the redirect is followed.
        return self._transport.request_bytes(
            "GET", f"{self._path}/files/{path}", kind=CqsKind.QUERY, follow_redirects=True
        )

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

    # GET .../snippets/{workspace}/{encoded_id}/{revision}/patch
    def patch(self, revision: str) -> str:
        return self._transport.request_text("GET", f"{self._path}/{revision}/patch", kind=CqsKind.QUERY)

    def revision(self, node_id: str) -> SnippetRevision:
        return SnippetRevision(self._transport, self._path, node_id)

    # GET .../snippets/{workspace}/{encoded_id}/watchers (auto-paginating)
    def watchers(self) -> Iterator[Account]:
        return paginate(lambda cursor: self.watchers_page(cursor=cursor))

    # GET .../snippets/{workspace}/{encoded_id}/watchers
    def watchers_page(self, *, cursor: str | None = None) -> Page[Account]:
        data = self._transport.request("GET", cursor or f"{self._path}/watchers", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Account)


class SnippetRevision:
    # One revision of a snippet, /snippets/{workspace}/{encoded_id}/{node_id}. Only the
    # latest revision can be changed or deleted; an older one answers 405 (a
    # compare-and-swap guard against a concurrent edit).
    def __init__(self, transport: Transport, snippet_path: str, node_id: str) -> None:
        self.node_id = node_id
        self._transport = transport
        self._path = f"{snippet_path}/{node_id}"

    # DELETE .../snippets/{workspace}/{encoded_id}/{node_id}
    def delete(self) -> None:
        self._transport.request("DELETE", self._path, kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET .../snippets/{workspace}/{encoded_id}/{node_id}/files/{path}
    def file(self, path: str) -> bytes:
        return self._transport.request_bytes("GET", f"{self._path}/files/{path}", kind=CqsKind.QUERY)

    # GET .../snippets/{workspace}/{encoded_id}/{node_id}
    def get(self) -> Snippet:
        data = self._transport.request("GET", self._path, kind=CqsKind.QUERY)
        return Snippet.model_validate(data)

    # PUT .../snippets/{workspace}/{encoded_id}/{node_id}
    def update(
        self,
        payload: SnippetUpdate,
        *,
        files: Mapping[str, bytes] | None = None,
        delete_files: Sequence[str] = (),
    ) -> Snippet:
        return update_snippet(self._transport, self._path, payload, files, delete_files)
