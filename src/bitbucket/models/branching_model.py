from __future__ import annotations

from enum import StrEnum

from bitbucket.models.base import BitbucketModel
from bitbucket.models.branch import Branch
from bitbucket.models.link import Links


class BranchingModelKind(StrEnum):
    FEATURE = "feature"
    BUGFIX = "bugfix"
    RELEASE = "release"
    HOTFIX = "hotfix"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> BranchingModelKind:
        del value
        return cls.UNKNOWN


class BranchingModelBranchType(BitbucketModel):
    kind: BranchingModelKind | None = None
    prefix: str | None = None


class BranchingModelTarget(BitbucketModel):
    # `branch` is only present on a repository's model; the project variant omits it.
    name: str | None = None
    use_mainbranch: bool | None = None
    branch: Branch | None = None


class BranchingModel(BitbucketModel):
    branch_types: list[BranchingModelBranchType] | None = None
    development: BranchingModelTarget | None = None
    production: BranchingModelTarget | None = None
    links: Links | None = None


class BranchTypeSetting(BitbucketModel):
    kind: BranchingModelKind | None = None
    enabled: bool | None = None
    prefix: str | None = None


class BranchTargetSetting(BitbucketModel):
    name: str | None = None
    use_mainbranch: bool | None = None
    is_valid: bool | None = None
    enabled: bool | None = None


class BranchingModelSettings(BitbucketModel):
    branch_types: list[BranchTypeSetting] | None = None
    development: BranchTargetSetting | None = None
    production: BranchTargetSetting | None = None
    links: Links | None = None


class BranchTargetSettingUpdate(BitbucketModel):
    # No `is_valid`: the spec marks it read-only and ignored on write.
    name: str | None = None
    use_mainbranch: bool | None = None
    enabled: bool | None = None


class BranchingModelSettingsUpdate(BitbucketModel):
    branch_types: list[BranchTypeSetting] | None = None
    development: BranchTargetSettingUpdate | None = None
    production: BranchTargetSettingUpdate | None = None
