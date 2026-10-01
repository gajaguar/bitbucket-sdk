from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket.resources.pipelines_config import AccountPipelinesConfig
from bitbucket.resources.search import SearchResource

if TYPE_CHECKING:
    from bitbucket._transport import Transport


class TeamClient:
    # A thin wiring class like UserClient, for /teams/{username}; code search
    # and pipeline variables are what the spec still has under it.
    def __init__(self, transport: Transport, username: str) -> None:
        self.username = username
        self.search = SearchResource(transport, f"/teams/{username}")
        self.pipelines_config = AccountPipelinesConfig(transport, f"/teams/{username}")
