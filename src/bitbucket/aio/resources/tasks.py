from __future__ import annotations

from bitbucket.aio.resources.base import AsyncDeletableResourceMixin
from bitbucket.aio.resources.base import AsyncNestedResource
from bitbucket.models.task import Task
from bitbucket.models.task import TaskCreate
from bitbucket.models.task import TaskUpdate


class AsyncTasksResource(
    AsyncNestedResource[Task, TaskCreate, TaskUpdate],
    AsyncDeletableResourceMixin,
):
    _path = "/tasks"
    _read_model = Task
