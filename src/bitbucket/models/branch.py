from __future__ import annotations

from enum import StrEnum

from bitbucket.ids import CommitHash
from bitbucket.models.base import BitbucketModel
from bitbucket.models.link import Links


class MergeStrategy(StrEnum):
    MERGE_COMMIT = "merge_commit"
    SQUASH = "squash"
    FAST_FORWARD = "fast_forward"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> MergeStrategy:
        del value
        return cls.UNKNOWN


class RefTarget(BitbucketModel):
    # Deliberately not `models.commit.CommitRef`: that module imports
    # `models.repository`, which imports this module for `Repository.mainbranch`
    # — reusing it here would be a circular import.
    type: str | None = None
    hash: CommitHash | None = None


class Branch(BitbucketModel):
    name: str | None = None
    target: RefTarget | None = None
    merge_strategies: list[str] | None = None
    default_merge_strategy: MergeStrategy | None = None
    type: str | None = None
    links: Links | None = None


class RefTargetSpec(BitbucketModel):
    hash: str


class BranchCreate(BitbucketModel):
    name: str
    target: RefTargetSpec
