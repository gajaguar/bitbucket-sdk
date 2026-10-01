from __future__ import annotations

from bitbucket.aio.resources.base import AsyncDeletableResourceMixin
from bitbucket.aio.resources.base import AsyncNestedResource
from bitbucket.models.runner import Runner
from bitbucket.models.runner import RunnerCreate
from bitbucket.models.runner import RunnerUpdate


class AsyncRunnersResource(AsyncNestedResource[Runner, RunnerCreate, RunnerUpdate], AsyncDeletableResourceMixin):
    # Repository and workspace runners share this class; the base path ends in
    # `pipelines-config`.
    _path = "/runners"
    _read_model = Runner
