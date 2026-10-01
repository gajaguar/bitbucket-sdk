from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.search import CodeSearchResult
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport


class SearchResource:
    # One resource for the workspace, user and team search routes, which share
    # their parameters and response. The spec deprecates all three on 2026-11-01.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/search/code"

    # GET {path}/search/code (auto-paginating)
    def code(
        self,
        search_query: str,
        *,
        fields: str | None = None,
        pagelen: int | None = None,
    ) -> Iterator[CodeSearchResult]:
        return paginate(lambda cursor: self.code_page(search_query, fields=fields, pagelen=pagelen, cursor=cursor))

    # GET {path}/search/code
    def code_page(
        self,
        search_query: str,
        *,
        fields: str | None = None,
        pagelen: int | None = None,
        cursor: str | None = None,
    ) -> Page[CodeSearchResult]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            params = {"search_query": search_query, "fields": fields, "pagelen": pagelen}
            data = self._transport.request("GET", self._path, kind=CqsKind.QUERY, params=params)
        return page_from_payload(cast("dict[str, Any]", data), CodeSearchResult)
