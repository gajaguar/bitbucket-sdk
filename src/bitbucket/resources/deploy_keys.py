from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.deploy_key import DeployKey
from bitbucket.models.deploy_key import DeployKeyCreate
from bitbucket.models.deploy_key import DeployKeyUpdate
from bitbucket.models.deploy_key import ProjectDeployKey
from bitbucket.resources.base import DeletableResourceMixin
from bitbucket.resources.base import NestedResource
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport


class DeployKeysResource(
    NestedResource[DeployKey, DeployKeyCreate, DeployKeyUpdate],
    DeletableResourceMixin,
):
    _path = "/deploy-keys"
    _read_model = DeployKey


class ProjectDeployKeysResource:
    # Not a NestedResource: the spec has no PUT for a project deploy key, and
    # NestedResource would expose an `update` with nothing to call.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/deploy-keys"

    # POST {path}
    def create(self, payload: DeployKeyCreate) -> ProjectDeployKey:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request("POST", self._path, kind=CqsKind.NON_IDEMPOTENT_COMMAND, json=body)
        return ProjectDeployKey.model_validate(data)

    # DELETE {path}/{key_id}
    def delete(self, key_id: object) -> None:
        self._transport.request("DELETE", f"{self._path}/{key_id}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET {path}/{key_id}
    def get(self, key_id: object) -> ProjectDeployKey:
        data = self._transport.request("GET", f"{self._path}/{key_id}", kind=CqsKind.QUERY)
        return ProjectDeployKey.model_validate(data)

    # GET {path} (auto-paginating)
    def list(self) -> Iterator[ProjectDeployKey]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    def list_page(self, *, cursor: str | None = None) -> Page[ProjectDeployKey]:
        data = self._transport.request("GET", cursor or self._path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), ProjectDeployKey)
