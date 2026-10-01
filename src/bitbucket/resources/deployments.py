from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.deployment import Deployment
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport


class DeploymentsResource:
    # Read-only: the spec has no operation to create or change a deployment.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/deployments"

    # GET {path}/{deployment_uuid}
    def get(self, deployment_uuid: object) -> Deployment:
        data = self._transport.request("GET", f"{self._path}/{deployment_uuid}", kind=CqsKind.QUERY)
        return Deployment.model_validate(data)

    # GET {path} (auto-paginating)
    def list(self) -> Iterator[Deployment]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    def list_page(self, *, cursor: str | None = None) -> Page[Deployment]:
        data = self._transport.request("GET", cursor or self._path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Deployment)
