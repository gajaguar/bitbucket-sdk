from __future__ import annotations

from typing import Self

from bitbucket._auth import BasicAuth
from bitbucket._transport import Transport
from bitbucket.config import DEFAULT_BASE_URL
from bitbucket.config import ClientConfig
from bitbucket.config import ClientOptions
from bitbucket.config import resolve_credentials
from bitbucket.config import resolve_workspace
from bitbucket.ids import WorkspaceSlug
from bitbucket.resources.user import UserResource
from bitbucket.retry import RetryPolicy
from bitbucket.workspace import WorkspaceClient


class BitbucketClient:
    def __init__(
        self,
        email: str | None = None,
        api_token: str | None = None,
        *,
        options: ClientOptions | None = None,
    ) -> None:
        resolved_options = options or ClientOptions()
        resolved_email, resolved_token = resolve_credentials(email, api_token)
        self._config = ClientConfig(
            email=resolved_email,
            api_token=resolved_token,
            base_url=resolved_options.base_url or DEFAULT_BASE_URL,
            timeout=resolved_options.timeout,
            retry=resolved_options.retry or RetryPolicy(),
            event_hooks=resolved_options.event_hooks,
        )
        self._transport = Transport(self._config, BasicAuth(resolved_email, resolved_token))
        self.user = UserResource(self._transport)

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
