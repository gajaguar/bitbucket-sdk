from __future__ import annotations

from enum import StrEnum

from bitbucket.models.base import BitbucketModel
from bitbucket.models.branch import MergeStrategy
from bitbucket.models.pull_request import PullRequest


class MergeTaskState(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> MergeTaskState:
        del value
        return cls.UNKNOWN


class MergeParameters(BitbucketModel):
    # Write-side POST .../merge body. `type` is fixed by Bitbucket's API
    # contract and is not user-settable, so it is not modeled here.
    message: str | None = None
    close_source_branch: bool | None = None
    merge_strategy: MergeStrategy | None = None


class MergeTask(BitbucketModel):
    # 202 Accepted body: identifies the async merge task to poll.
    task_id: str | None = None


class MergeTaskStatus(BitbucketModel):
    task_status: MergeTaskState | None = None
    message: str | None = None
    pull_request: PullRequest | None = None
