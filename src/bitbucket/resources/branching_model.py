from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket.models.branching_model import BranchingModel
from bitbucket.models.branching_model import BranchingModelSettings
from bitbucket.models.branching_model import BranchingModelSettingsUpdate
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from bitbucket._transport import Transport


class BranchingModelResource:
    # A single-document resource under a repository or a project — no {id}, so it
    # doesn't fit NestedResource's shape — hand-written like
    # RepositoryPermissionsResource.override_settings.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._base_path = base_path

    # GET {base_path}/branching-model
    def get(self) -> BranchingModel:
        data = self._transport.request("GET", f"{self._base_path}/branching-model", kind=CqsKind.QUERY)
        return BranchingModel.model_validate(data)

    # GET {base_path}/branching-model/settings
    def settings(self) -> BranchingModelSettings:
        data = self._transport.request("GET", f"{self._base_path}/branching-model/settings", kind=CqsKind.QUERY)
        return BranchingModelSettings.model_validate(data)

    # PUT {base_path}/branching-model/settings
    def update_settings(self, payload: BranchingModelSettingsUpdate) -> BranchingModelSettings:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        path = f"{self._base_path}/branching-model/settings"
        data = self._transport.request("PUT", path, kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
        return BranchingModelSettings.model_validate(data)


class RepositoryBranchingModelResource(BranchingModelResource):
    # Only a repository has an effective model; a project's own model is what its
    # repositories inherit.
    # GET {base_path}/effective-branching-model
    def effective(self) -> BranchingModel:
        data = self._transport.request("GET", f"{self._base_path}/effective-branching-model", kind=CqsKind.QUERY)
        return BranchingModel.model_validate(data)
