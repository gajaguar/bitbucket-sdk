from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.account import User
from bitbucket.models.user_email import UserEmail
from bitbucket.models.workspace import WorkspaceAccess
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport


class UserResource:
    # Root-level, not workspace- or repo-scoped — hand-written per the
    # over-abstraction guard in docs/TECH_SPEC.md.
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    # GET /user
    def me(self) -> User:
        data = self._transport.request("GET", "/user", kind=CqsKind.QUERY)
        return User.model_validate(data)

    # GET .../user/emails (auto-paginating)
    def emails(self) -> Iterator[UserEmail]:
        return paginate(lambda cursor: self.emails_page(cursor=cursor))

    # GET .../user/emails
    def emails_page(self, *, cursor: str | None = None) -> Page[UserEmail]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", "/user/emails", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), UserEmail)

    # GET .../user/emails/{email}
    def email(self, address: str) -> UserEmail:
        data = self._transport.request("GET", f"/user/emails/{address}", kind=CqsKind.QUERY)
        return UserEmail.model_validate(data)

    # GET .../user/workspaces (auto-paginating)
    def workspaces(
        self,
        *,
        administrator: bool | None = None,
        sort: str | None = None,
        q: str | None = None,
    ) -> Iterator[WorkspaceAccess]:
        return paginate(
            lambda cursor: self.workspaces_page(administrator=administrator, sort=sort, q=q, cursor=cursor)
        )

    # GET .../user/workspaces
    def workspaces_page(
        self,
        *,
        administrator: bool | None = None,
        sort: str | None = None,
        q: str | None = None,
        cursor: str | None = None,
    ) -> Page[WorkspaceAccess]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            params = {"administrator": administrator, "sort": sort, "q": q}
            data = self._transport.request("GET", "/user/workspaces", kind=CqsKind.QUERY, params=params)
        return page_from_payload(cast("dict[str, Any]", data), WorkspaceAccess)
