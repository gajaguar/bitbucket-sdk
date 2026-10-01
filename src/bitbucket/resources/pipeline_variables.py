from __future__ import annotations

from bitbucket.models.pipeline_variable import PipelineVariable
from bitbucket.models.pipeline_variable import PipelineVariableCreate
from bitbucket.models.pipeline_variable import PipelineVariableUpdate
from bitbucket.resources.base import DeletableResourceMixin
from bitbucket.resources.base import NestedResource


class PipelineVariablesResource(
    NestedResource[PipelineVariable, PipelineVariableCreate, PipelineVariableUpdate],
    DeletableResourceMixin,
):
    # One class for the repository, workspace, team and user scopes: the shape is
    # the same and only the config segment of the base path differs
    # (`pipelines_config` vs the workspace's `pipelines-config`).
    _path = "/variables"
    _read_model = PipelineVariable
