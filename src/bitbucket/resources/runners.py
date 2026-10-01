from __future__ import annotations

from bitbucket.models.runner import Runner
from bitbucket.models.runner import RunnerCreate
from bitbucket.models.runner import RunnerUpdate
from bitbucket.resources.base import DeletableResourceMixin
from bitbucket.resources.base import NestedResource


class RunnersResource(NestedResource[Runner, RunnerCreate, RunnerUpdate], DeletableResourceMixin):
    # Repository and workspace runners share this class; the base path ends in
    # `pipelines-config`.
    _path = "/runners"
    _read_model = Runner
