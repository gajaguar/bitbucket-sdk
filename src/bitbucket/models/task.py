from __future__ import annotations

from typing import Literal

from bitbucket._time import BitbucketInstant
from bitbucket.ids import TaskId
from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.link import Links
from bitbucket.models.pull_request import RenderedField

type TaskState = Literal["RESOLVED", "UNRESOLVED"]  # pylint: disable=app-module-const-naming


class Task(BitbucketModel):
    id: TaskId | None = None
    content: RenderedField | None = None
    state: TaskState | None = None
    created_on: BitbucketInstant | None = None
    updated_on: BitbucketInstant | None = None
    creator: Account | None = None
    resolved_by: Account | None = None
    pending: bool | None = None
    links: Links | None = None


class TaskContentCreate(BitbucketModel):
    raw: str


class TaskCreate(BitbucketModel):
    content: TaskContentCreate
    pending: bool | None = None


class TaskUpdate(BitbucketModel):
    content: TaskContentCreate | None = None
    state: TaskState | None = None
