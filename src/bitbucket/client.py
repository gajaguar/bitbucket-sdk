from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Self

from bitbucket._auth import auth_for
from bitbucket._transport import Transport
from bitbucket.config import DEFAULT_BASE_URL
from bitbucket.config import ClientConfig
from bitbucket.config import ClientOptions
from bitbucket.config import resolve_credentials
from bitbucket.config import resolve_workspace
from bitbucket.ids import WorkspaceSlug
from bitbucket.resources.hook_events import HookEventsResource
from bitbucket.resources.user import UserResource
from bitbucket.retry import RetryPolicy
from bitbucket.team import TeamClient
from bitbucket.user import UserClient
from bitbucket.workspace import WorkspaceClient

if TYPE_CHECKING:
    from bitbucket.config import AccessTokenProvider
    from bitbucket.config import ApiTokenProvider


def _build_config(
    email: str | None,
    api_token: str | ApiTokenProvider | None,
    access_token: str | AccessTokenProvider | None,
    options: ClientOptions | None,
) -> ClientConfig:
    resolved_options = options or ClientOptions()
    credentials = resolve_credentials(email, api_token, access_token)
    return ClientConfig(
        credentials=credentials,
        base_url=resolved_options.base_url or DEFAULT_BASE_URL,
        timeout=resolved_options.timeout,
        retry=resolved_options.retry or RetryPolicy(),
        event_hooks=resolved_options.event_hooks,
    )


class BitbucketClient:
    def __init__(
        self,
        email: str | None = None,
        api_token: str | ApiTokenProvider | None = None,
        *,
        access_token: str | AccessTokenProvider | None = None,
        options: ClientOptions | None = None,
    ) -> None:
        self._config = _build_config(email, api_token, access_token, options)
        self._transport = Transport(self._config, auth_for(self._config.credentials))
        self.user = UserResource(self._transport)
        self.hook_events = HookEventsResource(self._transport)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._transport.close()

    def default_workspace(self) -> WorkspaceClient:
        return self.workspace(resolve_workspace(None))

    def workspace(self, slug: WorkspaceSlug | str) -> WorkspaceClient:
        return WorkspaceClient(self._transport, WorkspaceSlug(str(slug)))

    def users(self, selected_user: str) -> UserClient:
        return UserClient(self._transport, selected_user)

    def teams(self, username: str) -> TeamClient:
        return TeamClient(self._transport, username)
