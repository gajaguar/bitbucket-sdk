from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.models.search import CodeSearchResult
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport


class AsyncSearchResource:
    # One resource for the workspace, user and team search routes, which share
    # their parameters and response. The spec deprecates all three on 2026-11-01.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/search/code"

    # GET {path}/search/code (auto-paginating)
    def code(
        self,
        search_query: str,
        *,
        fields: str | None = None,
        pagelen: int | None = None,
    ) -> AsyncIterator[CodeSearchResult]:
        return apaginate(lambda cursor: self.code_page(search_query, fields=fields, pagelen=pagelen, cursor=cursor))

    # GET {path}/search/code
    async def code_page(
        self,
        search_query: str,
        *,
        fields: str | None = None,
        pagelen: int | None = None,
        cursor: str | None = None,
    ) -> Page[CodeSearchResult]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            params = {"search_query": search_query, "fields": fields, "pagelen": pagelen}
            data = await self._transport.request("GET", self._path, kind=CqsKind.QUERY, params=params)
        return page_from_payload(cast("dict[str, Any]", data), CodeSearchResult)
