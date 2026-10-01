from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket.models.branching_model import BranchingModel
from bitbucket.models.branching_model import BranchingModelSettings
from bitbucket.models.branching_model import BranchingModelSettingsUpdate
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from bitbucket.aio._transport import AsyncTransport


class AsyncBranchingModelResource:
    # Async mirror of BranchingModelResource — see that class's comment.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._base_path = base_path

    # GET {base_path}/branching-model
    async def get(self) -> BranchingModel:
        data = await self._transport.request("GET", f"{self._base_path}/branching-model", kind=CqsKind.QUERY)
        return BranchingModel.model_validate(data)

    # GET {base_path}/branching-model/settings
    async def settings(self) -> BranchingModelSettings:
        data = await self._transport.request("GET", f"{self._base_path}/branching-model/settings", kind=CqsKind.QUERY)
        return BranchingModelSettings.model_validate(data)

    # PUT {base_path}/branching-model/settings
    async def update_settings(self, payload: BranchingModelSettingsUpdate) -> BranchingModelSettings:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        path = f"{self._base_path}/branching-model/settings"
        data = await self._transport.request("PUT", path, kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
        return BranchingModelSettings.model_validate(data)


class AsyncRepositoryBranchingModelResource(AsyncBranchingModelResource):
    # GET {base_path}/effective-branching-model
    async def effective(self) -> BranchingModel:
        data = await self._transport.request("GET", f"{self._base_path}/effective-branching-model", kind=CqsKind.QUERY)
        return BranchingModel.model_validate(data)
