from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
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
    from collections.abc import AsyncIterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket.aio._transport import AsyncTransport
    from bitbucket.models.base import BitbucketModel


class AsyncGroupPermissionsBase[ReadT: BitbucketModel, UpdateT: BitbucketModel]:
    _read_model: type[ReadT]

    # {id} item path uses a group slug, and updates take a bare
    # `{"permission": ...}` body rather than the full group object — doesn't
    # fit AsyncNestedResource's shape — hand-written per the over-abstraction
    # guard in docs/TECH_SPEC.md.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/permissions-config/groups"

    # GET {path} (auto-paginating)
    def list(self) -> AsyncIterator[ReadT]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    async def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[ReadT]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), self._read_model)

    # GET {path}/{group_slug}
    async def get(self, group_slug: str) -> ReadT:
        data = await self._transport.request("GET", f"{self._path}/{group_slug}", kind=CqsKind.QUERY)
        return self._read_model.model_validate(data)

    # PUT {path}/{group_slug}
    async def update(self, group_slug: str, payload: UpdateT) -> ReadT:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request(
            "PUT", f"{self._path}/{group_slug}", kind=CqsKind.IDEMPOTENT_COMMAND, json=body
        )
        return self._read_model.model_validate(data)

    # DELETE {path}/{group_slug}
    async def delete(self, group_slug: str) -> None:
        await self._transport.request("DELETE", f"{self._path}/{group_slug}", kind=CqsKind.IDEMPOTENT_COMMAND)


class AsyncUserPermissionsBase[ReadT: BitbucketModel, UpdateT: BitbucketModel]:
    _read_model: type[ReadT]

    # Same shape as AsyncGroupPermissionsResource, keyed by account id instead of
    # group slug — hand-written for the same reason.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/permissions-config/users"

    # GET {path} (auto-paginating)
    def list(self) -> AsyncIterator[ReadT]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    async def list_page(self, *, cursor: str | None = None, pagelen: int = 100) -> Page[ReadT]:
        if cursor:
            data = await self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = await self._transport.request("GET", self._path, kind=CqsKind.QUERY, params={"pagelen": pagelen})
        return page_from_payload(cast("dict[str, Any]", data), self._read_model)

    # GET {path}/{account_id}
    async def get(self, account_id: str) -> ReadT:
        data = await self._transport.request("GET", f"{self._path}/{account_id}", kind=CqsKind.QUERY)
        return self._read_model.model_validate(data)

    # PUT {path}/{account_id}
    async def update(self, account_id: str, payload: UpdateT) -> ReadT:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request(
            "PUT", f"{self._path}/{account_id}", kind=CqsKind.IDEMPOTENT_COMMAND, json=body
        )
        return self._read_model.model_validate(data)

    # DELETE {path}/{account_id}
    async def delete(self, account_id: str) -> None:
        await self._transport.request("DELETE", f"{self._path}/{account_id}", kind=CqsKind.IDEMPOTENT_COMMAND)


class AsyncGroupPermissionsResource(AsyncGroupPermissionsBase[GroupPermission, GroupPermissionUpdate]):
    _read_model = GroupPermission


class AsyncUserPermissionsResource(AsyncUserPermissionsBase[UserPermission, UserPermissionUpdate]):
    _read_model = UserPermission


class AsyncProjectGroupPermissionsResource(AsyncGroupPermissionsBase[ProjectGroupPermission, ProjectPermissionUpdate]):
    _read_model = ProjectGroupPermission


class AsyncProjectUserPermissionsResource(AsyncUserPermissionsBase[ProjectUserPermission, ProjectPermissionUpdate]):
    _read_model = ProjectUserPermission


class AsyncProjectPermissionsResource:
    # Project permissions have no override-settings sibling, so unlike the
    # repository umbrella this one is only the two permissions-config collections.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self.groups = AsyncProjectGroupPermissionsResource(transport, base_path)
        self.users = AsyncProjectUserPermissionsResource(transport, base_path)


class AsyncRepositoryPermissionsResource:
    # Umbrella over the permissions-config sub-resources — groups: and users:
    # are keyed collections; override_settings (a sibling path, not under
    # permissions-config) is a single-document resource, so none share AsyncNestedResource's {path}/{id} shape.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._base_path = base_path
        self.groups = AsyncGroupPermissionsResource(transport, base_path)
        self.users = AsyncUserPermissionsResource(transport, base_path)

    # GET .../override-settings
    async def override_settings(self) -> RepositoryInheritanceState:
        data = await self._transport.request("GET", f"{self._base_path}/override-settings", kind=CqsKind.QUERY)
        return RepositoryInheritanceState.model_validate(data)

    # PUT .../override-settings (204, no body)
    async def update_override_settings(self, payload: RepositoryOverrideSettings) -> None:
        settings = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        body: dict[str, Any] = {"override_settings": settings}
        await self._transport.request(
            "PUT", f"{self._base_path}/override-settings", kind=CqsKind.IDEMPOTENT_COMMAND, json=body
        )
