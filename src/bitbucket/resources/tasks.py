from __future__ import annotations

from bitbucket.models.task import Task
from bitbucket.models.task import TaskCreate
from bitbucket.models.task import TaskUpdate
from bitbucket.resources.base import DeletableResourceMixin
from bitbucket.resources.base import NestedResource


class TasksResource(NestedResource[Task, TaskCreate, TaskUpdate], DeletableResourceMixin):
    _path = "/tasks"
    _read_model = Task
