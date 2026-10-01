from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.models.deployment import Deployment
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport


class AsyncDeploymentsResource:
    # Read-only: the spec has no operation to create or change a deployment.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/deployments"

    # GET {path}/{deployment_uuid}
    async def get(self, deployment_uuid: object) -> Deployment:
        data = await self._transport.request("GET", f"{self._path}/{deployment_uuid}", kind=CqsKind.QUERY)
        return Deployment.model_validate(data)

    # GET {path} (auto-paginating)
    def list(self) -> AsyncIterator[Deployment]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    async def list_page(self, *, cursor: str | None = None) -> Page[Deployment]:
        data = await self._transport.request("GET", cursor or self._path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Deployment)
