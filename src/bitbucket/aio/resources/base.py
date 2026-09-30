from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    import builtins
    from collections.abc import AsyncIterator

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport
    from bitbucket.models.base import BitbucketModel


__all__ = ["AsyncDeletableResourceMixin", "AsyncNestedResource", "page_from_payload"]


class AsyncNestedResource[ReadT: BitbucketModel, CreateT: BitbucketModel, UpdateT: BitbucketModel]:
    # Async mirror of resources.base.NestedResource — see that class's docstring
    # for the contract; auto-paginating methods yield AsyncIterator[T] via apaginate.
    _path: str
    _read_model: type[ReadT]

    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._base_path = base_path

    # POST {path}
    async def create(self, payload: CreateT) -> ReadT:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request(
            "POST", self._collection_path(), kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body
        )
        return self._read_model.model_validate(data)

    # GET {path}/{id}
    async def get(self, item_id: object) -> ReadT:
        data = await self._transport.request("GET", self._item_path(item_id), kind=CqsKind.QUERY)
        return self._read_model.model_validate(data)

    # GET {path} (auto-paginating)
    # `builtins.list` is used explicitly here and in list_page: this method is
    # named `list`, which shadows the builtin `list[str]` type in the rest of
    # this class's annotations.
    def list(self, **params: str | float | bool | builtins.list[str]) -> AsyncIterator[ReadT]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor, **params))

    # GET {path}
    async def list_page(
        self,
        *,
        cursor: str | None = None,
        **params: str | float | bool | builtins.list[str],
    ) -> Page[ReadT]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request(
                "GET", self._collection_path(), kind=CqsKind.QUERY, params=params or None
            )
        return page_from_payload(cast("dict[str, Any]", data), self._read_model)

    # PUT {path}/{id}
    async def update(self, item_id: object, payload: UpdateT) -> ReadT:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request(
            "PUT", self._item_path(item_id), kind=CqsKind.IDEMPOTENT_COMMAND, json=body
        )
        return self._read_model.model_validate(data)

    def _collection_path(self) -> str:
        return f"{self._base_path}{self._path}"

    def _item_path(self, item_id: object) -> str:
        return f"{self._collection_path()}/{item_id}"


class AsyncDeletableResourceMixin:
    # Declares the shape AsyncNestedResource provides, so mypy accepts the mixin without
    # a type: ignore at the call site below (composed as AsyncDeletableResourceMixin +
    # AsyncNestedResource[...] — see resources/comments.py).
    _transport: AsyncTransport

    def _item_path(self, item_id: object) -> str:
        raise NotImplementedError

    # DELETE {path}/{id}
    async def delete(self, item_id: object) -> None:
        await self._transport.request("DELETE", self._item_path(item_id), kind=CqsKind.IDEMPOTENT_COMMAND)
