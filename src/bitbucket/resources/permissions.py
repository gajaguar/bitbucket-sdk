from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.permission import GroupPermission
from bitbucket.models.permission import GroupPermissionUpdate
from bitbucket.models.permission import ProjectGroupPermission
from bitbucket.models.permission import ProjectPermissionUpdate
from bitbucket.models.permission import ProjectUserPermission
from bitbucket.models.permission import RepositoryInheritanceState
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
    from bitbucket.models.base import BitbucketModel


class GroupPermissionsBase[ReadT: BitbucketModel, UpdateT: BitbucketModel]:
    _read_model: type[ReadT]

    # {id} item path uses a group slug, and updates take a bare
    # `{"permission": ...}` body rather than the full group object — doesn't
    # fit NestedResource's shape — hand-written per the over-abstraction
    # guard in docs/TECH_SPEC.md.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/permissions-config/groups"

    # GET {path} (auto-paginating)
    def list(self) -> Iterator[ReadT]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[ReadT]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), self._read_model)

    # GET {path}/{group_slug}
    def get(self, group_slug: str) -> ReadT:
        data = self._transport.request("GET", f"{self._path}/{group_slug}", kind=CqsKind.QUERY)
        return self._read_model.model_validate(data)

    # PUT {path}/{group_slug}
    def update(self, group_slug: str, payload: UpdateT) -> ReadT:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request("PUT", f"{self._path}/{group_slug}", kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
        return self._read_model.model_validate(data)

    # DELETE {path}/{group_slug}
    def delete(self, group_slug: str) -> None:
        self._transport.request("DELETE", f"{self._path}/{group_slug}", kind=CqsKind.IDEMPOTENT_COMMAND)


class UserPermissionsBase[ReadT: BitbucketModel, UpdateT: BitbucketModel]:
    _read_model: type[ReadT]

    # Same shape as GroupPermissionsResource, keyed by account id instead of
    # group slug — hand-written for the same reason.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/permissions-config/users"

    # GET {path} (auto-paginating)
    def list(self) -> Iterator[ReadT]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[ReadT]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), self._read_model)

    # GET {path}/{account_id}
    def get(self, account_id: str) -> ReadT:
        data = self._transport.request("GET", f"{self._path}/{account_id}", kind=CqsKind.QUERY)
        return self._read_model.model_validate(data)

    # PUT {path}/{account_id}
    def update(self, account_id: str, payload: UpdateT) -> ReadT:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request("PUT", f"{self._path}/{account_id}", kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
        return self._read_model.model_validate(data)

    # DELETE {path}/{account_id}
    def delete(self, account_id: str) -> None:
        self._transport.request("DELETE", f"{self._path}/{account_id}", kind=CqsKind.IDEMPOTENT_COMMAND)


class GroupPermissionsResource(GroupPermissionsBase[GroupPermission, GroupPermissionUpdate]):
    _read_model = GroupPermission


class UserPermissionsResource(UserPermissionsBase[UserPermission, UserPermissionUpdate]):
    _read_model = UserPermission


class ProjectGroupPermissionsResource(GroupPermissionsBase[ProjectGroupPermission, ProjectPermissionUpdate]):
    _read_model = ProjectGroupPermission


class ProjectUserPermissionsResource(UserPermissionsBase[ProjectUserPermission, ProjectPermissionUpdate]):
    _read_model = ProjectUserPermission


class ProjectPermissionsResource:
    # Project permissions have no override-settings sibling, so unlike the
    # repository umbrella this one is only the two permissions-config collections.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self.groups = ProjectGroupPermissionsResource(transport, base_path)
        self.users = ProjectUserPermissionsResource(transport, base_path)


class RepositoryPermissionsResource:
    # Umbrella over the permissions-config sub-resources — groups: and users:
    # are keyed collections; override_settings (a sibling path, not under
    # permissions-config) is a single-document resource, so none share NestedResource's {path}/{id} shape.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._base_path = base_path
        self.groups = GroupPermissionsResource(transport, base_path)
        self.users = UserPermissionsResource(transport, base_path)

    # GET .../override-settings
    def override_settings(self) -> RepositoryInheritanceState:
        data = self._transport.request("GET", f"{self._base_path}/override-settings", kind=CqsKind.QUERY)
        return RepositoryInheritanceState.model_validate(data)

    # PUT .../override-settings (204, no body)
    def update_override_settings(self, payload: RepositoryOverrideSettings) -> None:
        settings = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        body: dict[str, Any] = {"override_settings": settings}
        self._transport.request(
            "PUT", f"{self._base_path}/override-settings", kind=CqsKind.IDEMPOTENT_COMMAND, json=body
        )
