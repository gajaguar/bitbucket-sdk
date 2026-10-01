from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket.aio.resources.gpg_keys import AsyncGpgKeysResource
from bitbucket.aio.resources.pipelines_config import AsyncAccountPipelinesConfig
from bitbucket.aio.resources.properties import AsyncPropertiesResource
from bitbucket.aio.resources.search import AsyncSearchResource
from bitbucket.aio.resources.ssh_keys import AsyncSshKeysResource
from bitbucket.models.account import User
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from bitbucket.aio._transport import AsyncTransport


class AsyncUserClient:
    # A thin wiring class like AsyncProjectClient, for /users/{selected_user}.
    def __init__(self, transport: AsyncTransport, selected_user: str) -> None:
        self.selected_user = selected_user
        self._transport = transport
        self._path = f"/users/{selected_user}"
        self.ssh_keys = AsyncSshKeysResource(transport, self._path)
        self.gpg_keys = AsyncGpgKeysResource(transport, self._path)
        self.search = AsyncSearchResource(transport, self._path)
        self.pipelines_config = AsyncAccountPipelinesConfig(transport, self._path)
        self.properties = AsyncPropertiesResource(transport, self._path)

    # GET .../users/{selected_user}
    async def get(self) -> User:
        data = await self._transport.request("GET", self._path, kind=CqsKind.QUERY)
        return User.model_validate(data)
