from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.models.pipeline_variable import PipelineVariable
from bitbucket.models.pipeline_variable import PipelineVariableCreate
from bitbucket.models.pipeline_variable import PipelineVariableUpdate
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport


class AsyncDeploymentVariablesResource:
    # Not a NestedResource: the spec has no GET for a single deployment
    # variable, and `get` would have nothing to call.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/variables"

    # POST {path}
    async def create(self, payload: PipelineVariableCreate) -> PipelineVariable:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request("POST", self._path, kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body)
        return PipelineVariable.model_validate(data)

    # DELETE {path}/{variable_uuid}
    async def delete(self, variable_uuid: object) -> None:
        await self._transport.request("DELETE", f"{self._path}/{variable_uuid}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET {path} (auto-paginating)
    def list(self) -> AsyncIterator[PipelineVariable]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    async def list_page(self, *, cursor: str | None = None) -> Page[PipelineVariable]:
        data = await self._transport.request("GET", cursor or self._path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), PipelineVariable)

    # PUT {path}/{variable_uuid}
    async def update(self, variable_uuid: object, payload: PipelineVariableUpdate) -> PipelineVariable:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request(
            "PUT", f"{self._path}/{variable_uuid}", kind=CqsKind.IDEMPOTENT_COMMAND, json=body
        )
        return PipelineVariable.model_validate(data)


class AsyncEnvironmentsResource:
    # 4a only reaches environments through their variables; the environment
    # operations themselves (Deployments) land here in Phase 4b.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._base_path = base_path

    def variables(self, environment_uuid: object) -> AsyncDeploymentVariablesResource:
        base = f"{self._base_path}/deployments_config/environments/{environment_uuid}"
        return AsyncDeploymentVariablesResource(self._transport, base)
