from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from bitbucket._transport import JSONValue
    from bitbucket.aio._transport import AsyncTransport


class AsyncPropertiesResource:
    # Connect-app storage: GET/PUT/DELETE {app_key}/{property_name}, no
    # collection endpoint and no fixed value schema (the stored value is
    # whatever JSON the app wrote) — hand-written per the over-abstraction
    # guard in docs/TECH_SPEC.md.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._base_path = f"{base_path}/properties"

    # GET {path}/{app_key}/{property_name}
    async def get(self, app_key: str, property_name: str) -> JSONValue:
        return await self._transport.request("GET", self._item_path(app_key, property_name), kind=CqsKind.QUERY)

    # PUT {path}/{app_key}/{property_name}
    async def put(self, app_key: str, property_name: str, value: JSONValue) -> JSONValue:
        return await self._transport.request(
            "PUT", self._item_path(app_key, property_name), kind=CqsKind.IDEMPOTENT_COMMAND, json=value
        )

    # DELETE {path}/{app_key}/{property_name}
    async def delete(self, app_key: str, property_name: str) -> None:
        await self._transport.request(
            "DELETE", self._item_path(app_key, property_name), kind=CqsKind.IDEMPOTENT_COMMAND
        )

    def _item_path(self, app_key: str, property_name: str) -> str:
        return f"{self._base_path}/{app_key}/{property_name}"
