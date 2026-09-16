from __future__ import annotations

from typing import Literal

from bitbucket._time import BitbucketInstant
from bitbucket.models.base import BitbucketModel

type PullRequestStatusState = Literal[  # pylint: disable=app-module-const-naming
    "FAILED", "INPROGRESS", "STOPPED", "SUCCESSFUL"
]


class PullRequestStatus(BitbucketModel):
    key: str | None = None
    name: str | None = None
    state: PullRequestStatusState | None = None
    description: str | None = None
    url: str | None = None
    created_on: BitbucketInstant | None = None
    updated_on: BitbucketInstant | None = None


class PullRequestStatusCreate(BitbucketModel):
    key: str
    state: PullRequestStatusState
    name: str | None = None
    url: str | None = None
    description: str | None = None
