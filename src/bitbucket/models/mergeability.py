from __future__ import annotations

from enum import StrEnum
from typing import Any

from bitbucket.models.base import BitbucketModel
from bitbucket.models.link import Links


class MergeabilityCheckType(StrEnum):
    PULLREQUEST_STATE_CHECK = "pullrequest_state_check"
    CURRENT_USER_PERMISSION_CHECK = "current_user_permission_check"
    GIT_MERGEABILITY_CHECK = "git_mergeability_check"
    STANDARD_MERGE_CHECK = "standard_merge_check"
    CUSTOM_PRE_MERGE_CHECK = "custom_pre_merge_check"
    CUSTOM_ON_MERGE_CHECK = "custom_on_merge_check"
    MERGE_QUEUE_CHECK = "merge_queue_check"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> MergeabilityCheckType:
        del value
        return cls.UNKNOWN


class MergeabilityCheckStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    SKIPPED = "SKIPPED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> MergeabilityCheckStatus:
        del value
        return cls.UNKNOWN


class MergeabilityPullRequestState(StrEnum):
    OPEN = "OPEN"
    DRAFT = "DRAFT"
    MERGED = "MERGED"
    DECLINED = "DECLINED"
    SUPERSEDED = "SUPERSEDED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> MergeabilityPullRequestState:
        del value
        return cls.UNKNOWN


class GitMergeabilityReason(StrEnum):
    CLEAN = "clean"
    CONFLICTS = "conflicts"
    MERGE_IMPOSSIBLE = "merge_impossible"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> GitMergeabilityReason:
        del value
        return cls.UNKNOWN


class MergeCheckDefinition(BitbucketModel):
    type: str | None = None
    kind: str | None = None
    id: str | None = None
    name: str | None = None


class MergeQueue(BitbucketModel):
    type: str | None = None
    uuid: str | None = None
    name: str | None = None
    # Open string: the spec says unknown values are returned unchanged.
    state: str | None = None


class MergeabilityCheck(BitbucketModel):
    type: MergeabilityCheckType | None = None
    status: MergeabilityCheckStatus | None = None
    required: bool | None = None
    blocking: bool | None = None
    state: MergeabilityPullRequestState | None = None
    reason: GitMergeabilityReason | None = None
    links: Links | None = None
    check: MergeCheckDefinition | None = None
    requirement: dict[str, Any] | None = None
    observed: dict[str, Any] | None = None
    queued: bool | None = None
    merge_queue: MergeQueue | None = None
    uuid: str | None = None
    message: str | None = None
