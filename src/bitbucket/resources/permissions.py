from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.permission import GroupPermission
from bitbucket.models.permission import GroupPermissionUpdate
from bitbucket.models.permission import RepositoryOverrideSettings
from bitbucket.models.permission import UserPermission
from bitbucket.models.permission import UserPermissionUpdate
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport


class GroupPermissionsResource:
    # {id} item path uses a group slug, and updates take a bare
    # `{"permission": ...}` body rather than the full group object — doesn't
    # fit NestedResource's shape — hand-written per the over-abstraction
    # guard in docs/TECH_SPEC.md.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/permissions-config/groups"

    # GET {path} (auto-paginating)
    def list(self) -> Iterator[GroupPermission]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[GroupPermission]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), GroupPermission)

    # GET {path}/{group_slug}
    def get(self, group_slug: str) -> GroupPermission:
        data = self._transport.request("GET", f"{self._path}/{group_slug}", kind=CqsKind.QUERY)
        return GroupPermission.model_validate(data)

    # PUT {path}/{group_slug}
    def update(self, group_slug: str, payload: GroupPermissionUpdate) -> GroupPermission:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request("PUT", f"{self._path}/{group_slug}", kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
        return GroupPermission.model_validate(data)

    # DELETE {path}/{group_slug}
    def delete(self, group_slug: str) -> None:
        self._transport.request("DELETE", f"{self._path}/{group_slug}", kind=CqsKind.IDEMPOTENT_COMMAND)


class UserPermissionsResource:
    # Same shape as GroupPermissionsResource, keyed by account id instead of
    # group slug — hand-written for the same reason.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/permissions-config/users"

    # GET {path} (auto-paginating)
    def list(self) -> Iterator[UserPermission]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[UserPermission]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), UserPermission)

    # GET {path}/{account_id}
    def get(self, account_id: str) -> UserPermission:
        data = self._transport.request("GET", f"{self._path}/{account_id}", kind=CqsKind.QUERY)
        return UserPermission.model_validate(data)

    # PUT {path}/{account_id}
    def update(self, account_id: str, payload: UserPermissionUpdate) -> UserPermission:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request("PUT", f"{self._path}/{account_id}", kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
        return UserPermission.model_validate(data)

    # DELETE {path}/{account_id}
    def delete(self, account_id: str) -> None:
        self._transport.request("DELETE", f"{self._path}/{account_id}", kind=CqsKind.IDEMPOTENT_COMMAND)


class RepositoryPermissionsResource:
    # Umbrella over the three permissions-config sub-resources — groups: and
    # users: are keyed collections, override_settings is a single-document
    # resource, so none share NestedResource's {path}/{id} shape.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._base_path = base_path
        self.groups = GroupPermissionsResource(transport, base_path)
        self.users = UserPermissionsResource(transport, base_path)

    # GET .../permissions-config/override-settings
    def override_settings(self) -> RepositoryOverrideSettings:
        path = f"{self._base_path}/permissions-config/override-settings"
        data = self._transport.request("GET", path, kind=CqsKind.QUERY)
        return RepositoryOverrideSettings.model_validate(data)

    # PUT .../permissions-config/override-settings
    def update_override_settings(self, payload: RepositoryOverrideSettings) -> RepositoryOverrideSettings:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        path = f"{self._base_path}/permissions-config/override-settings"
        data = self._transport.request("PUT", path, kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
        return RepositoryOverrideSettings.model_validate(data)
