from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Self

from bitbucket._auth import auth_for
from bitbucket.aio._transport import AsyncTransport
from bitbucket.aio.resources.hook_events import AsyncHookEventsResource
from bitbucket.aio.resources.user import AsyncUserResource
from bitbucket.aio.team import AsyncTeamClient
from bitbucket.aio.user import AsyncUserClient
from bitbucket.aio.workspace import AsyncWorkspaceClient
from bitbucket.client import _build_config
from bitbucket.config import resolve_workspace
from bitbucket.ids import WorkspaceSlug

if TYPE_CHECKING:
    from bitbucket.config import AccessTokenProvider
    from bitbucket.config import ApiTokenProvider
    from bitbucket.config import ClientOptions


class AsyncBitbucketClient:
    def __init__(
        self,
        email: str | None = None,
        api_token: str | ApiTokenProvider | None = None,
        *,
        access_token: str | AccessTokenProvider | None = None,
        options: ClientOptions | None = None,
    ) -> None:
        self._config = _build_config(email, api_token, access_token, options)
        self._transport = AsyncTransport(self._config, auth_for(self._config.credentials))
        self.user = AsyncUserResource(self._transport)
        self.hook_events = AsyncHookEventsResource(self._transport)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._transport.aclose()

    def default_workspace(self) -> AsyncWorkspaceClient:
        return self.workspace(resolve_workspace(None))

    def workspace(self, slug: WorkspaceSlug | str) -> AsyncWorkspaceClient:
        return AsyncWorkspaceClient(self._transport, WorkspaceSlug(str(slug)))

    def users(self, selected_user: str) -> AsyncUserClient:
        return AsyncUserClient(self._transport, selected_user)

    def teams(self, username: str) -> AsyncTeamClient:
        return AsyncTeamClient(self._transport, username)
