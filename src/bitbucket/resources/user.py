from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket.models.account import Account
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from bitbucket._transport import Transport


class UserResource:
    # Root-level, not workspace- or repo-scoped — hand-written per the
    # over-abstraction guard in docs/TECH_SPEC.md.
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    # GET /user
    def me(self) -> Account:
        data = self._transport.request("GET", "/user", kind=CqsKind.QUERY)
        return Account.model_validate(data)
