from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from bitbucket._pagination import Page
from bitbucket._pagination import paginate
from bitbucket.models.base import BitbucketModel
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    import builtins
    from collections.abc import Iterator
    from collections.abc import Mapping

    from bitbucket._transport import Transport


def page_from_payload[ReadT: BitbucketModel](payload: Mapping[str, Any], read_model: type[ReadT]) -> Page[ReadT]:
    raw_items = cast("list[dict[str, Any]]", payload.get("values") or [])
    items = [read_model.model_validate(item) for item in raw_items]
    return Page(
        items=items,
        next_cursor=cast("str | None", payload.get("next")),
        size=cast("int | None", payload.get("size")),
    )


class NestedResource[ReadT: BitbucketModel, CreateT: BitbucketModel, UpdateT: BitbucketModel]:
    # Generic over any Bitbucket collection reachable as {base_path}{_path}[/{id}] —
    # a repository under a workspace, or a comment under a pull request, alike.
    # Bitbucket has no uniform DELETE-by-id verb across resources (pull requests
    # cannot be deleted, comments can), so `delete` lives on DeletableResourceMixin
    # rather than here — see resources/pull_requests.py and resources/comments.py.
    _path: str
    _read_model: type[ReadT]

    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._base_path = base_path

    # POST {path}
    def create(self, payload: CreateT) -> ReadT:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request("POST", self._collection_path(), kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body)
        return self._read_model.model_validate(data)

    # GET {path}/{id}
    def get(self, item_id: object) -> ReadT:
        data = self._transport.request("GET", self._item_path(item_id), kind=CqsKind.QUERY)
        return self._read_model.model_validate(data)

    # GET {path} (auto-paginating)
    # `builtins.list` is used explicitly here and in list_page: this method is
    # named `list`, which shadows the builtin `list[str]` type in the rest of
    # this class's annotations.
    def list(self, **params: str | float | bool | builtins.list[str]) -> Iterator[ReadT]:
        return paginate(lambda cursor: self.list_page(cursor=cursor, **params))

    # GET {path}
    def list_page(
        self,
        *,
        cursor: str | None = None,
        **params: str | float | bool | builtins.list[str],
    ) -> Page[ReadT]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", self._collection_path(), kind=CqsKind.QUERY, params=params or None)
        return page_from_payload(cast("dict[str, Any]", data), self._read_model)

    # PUT {path}/{id}
    def update(self, item_id: object, payload: UpdateT) -> ReadT:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request("PUT", self._item_path(item_id), kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
        return self._read_model.model_validate(data)

    def _collection_path(self) -> str:
        return f"{self._base_path}{self._path}"

    def _item_path(self, item_id: object) -> str:
        return f"{self._collection_path()}/{item_id}"


class DeletableResourceMixin:
    # Declares the shape NestedResource provides, so mypy accepts the mixin without
    # a type: ignore at the call site below (composed as DeletableResourceMixin +
    # NestedResource[...] — see resources/comments.py).
    _transport: Transport

    def _item_path(self, item_id: object) -> str:
        raise NotImplementedError

    # DELETE {path}/{id}
    def delete(self, item_id: object) -> None:
        self._transport.request("DELETE", self._item_path(item_id), kind=CqsKind.IDEMPOTENT_COMMAND)
