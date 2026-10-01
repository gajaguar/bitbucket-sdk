from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket.models.account import User
from bitbucket.resources.gpg_keys import GpgKeysResource
from bitbucket.resources.search import SearchResource
from bitbucket.resources.ssh_keys import SshKeysResource
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from bitbucket._transport import Transport


class UserClient:
    # A thin wiring class like ProjectClient, for /users/{selected_user}.
    def __init__(self, transport: Transport, selected_user: str) -> None:
        self.selected_user = selected_user
        self._transport = transport
        self._path = f"/users/{selected_user}"
        self.ssh_keys = SshKeysResource(transport, self._path)
        self.gpg_keys = GpgKeysResource(transport, self._path)
        self.search = SearchResource(transport, self._path)

    # GET .../users/{selected_user}
    def get(self) -> User:
        data = self._transport.request("GET", self._path, kind=CqsKind.QUERY)
        return User.model_validate(data)
