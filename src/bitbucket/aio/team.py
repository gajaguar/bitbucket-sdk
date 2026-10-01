from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket.aio.resources.search import AsyncSearchResource

if TYPE_CHECKING:
    from bitbucket.aio._transport import AsyncTransport


class AsyncTeamClient:
    # A thin wiring class like AsyncUserClient, for /teams/{username}; code
    # search is the only operation the spec still has under it.
    def __init__(self, transport: AsyncTransport, username: str) -> None:
        self.username = username
        self.search = AsyncSearchResource(transport, f"/teams/{username}")
