from __future__ import annotations

from enum import StrEnum

from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.link import Links
from bitbucket.models.permission import GroupRef
from bitbucket.models.pull_request import ReviewerSpec


class BranchRestrictionKind(StrEnum):
    PUSH = "push"
    DELETE = "delete"
    FORCE = "force"
    RESTRICT_MERGES = "restrict_merges"
    REQUIRE_TASKS_TO_BE_COMPLETED = "require_tasks_to_be_completed"
    REQUIRE_APPROVALS_TO_MERGE = "require_approvals_to_merge"
    REQUIRE_REVIEW_GROUP_APPROVALS_TO_MERGE = "require_review_group_approvals_to_merge"
    REQUIRE_DEFAULT_REVIEWER_APPROVALS_TO_MERGE = "require_default_reviewer_approvals_to_merge"
    REQUIRE_NO_CHANGES_REQUESTED = "require_no_changes_requested"
    REQUIRE_PASSING_BUILDS_TO_MERGE = "require_passing_builds_to_merge"
    REQUIRE_COMMITS_BEHIND = "require_commits_behind"
    RESET_PULLREQUEST_APPROVALS_ON_CHANGE = "reset_pullrequest_approvals_on_change"
    SMART_RESET_PULLREQUEST_APPROVALS = "smart_reset_pullrequest_approvals"
    RESET_PULLREQUEST_CHANGES_REQUESTED_ON_CHANGE = "reset_pullrequest_changes_requested_on_change"
    REQUIRE_ALL_DEPENDENCIES_MERGED = "require_all_dependencies_merged"
    ENFORCE_MERGE_CHECKS = "enforce_merge_checks"
    ALLOW_AUTO_MERGE_WHEN_BUILDS_PASS = "allow_auto_merge_when_builds_pass"  # ruff: ignore[hardcoded-password-string] -- a restriction kind, not a secret
    REQUIRE_ALL_COMMENTS_RESOLVED = "require_all_comments_resolved"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> BranchRestrictionKind:
        del value
        return cls.UNKNOWN


class BranchMatchKind(StrEnum):
    GLOB = "glob"
    BRANCHING_MODEL = "branching_model"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> BranchMatchKind:
        del value
        return cls.UNKNOWN


class BranchType(StrEnum):
    FEATURE = "feature"
    BUGFIX = "bugfix"
    RELEASE = "release"
    HOTFIX = "hotfix"
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> BranchType:
        del value
        return cls.UNKNOWN


class BranchRestriction(BitbucketModel):
    id: int | None = None
    kind: BranchRestrictionKind | None = None
    branch_match_kind: BranchMatchKind | None = None
    branch_type: BranchType | None = None
    pattern: str | None = None
    value: int | None = None
    pipelines_source_branches: list[str] | None = None
    users: list[Account] | None = None
    groups: list[GroupRef] | None = None
    links: Links | None = None


class BranchRestrictionCreate(BitbucketModel):
    # `branch_match_kind` and `pattern` are required by the spec's schema, but the
    # API defaults the match kind to `glob` and `branching_model` restrictions
    # carry no pattern — so only `kind` is mandatory here.
    kind: BranchRestrictionKind
    branch_match_kind: BranchMatchKind | None = None
    branch_type: BranchType | None = None
    pattern: str | None = None
    value: int | None = None
    pipelines_source_branches: list[str] | None = None
    users: list[ReviewerSpec] | None = None
    groups: list[GroupRef] | None = None


class BranchRestrictionUpdate(BitbucketModel):
    kind: BranchRestrictionKind | None = None
    branch_match_kind: BranchMatchKind | None = None
    branch_type: BranchType | None = None
    pattern: str | None = None
    value: int | None = None
    pipelines_source_branches: list[str] | None = None
    users: list[ReviewerSpec] | None = None
    groups: list[GroupRef] | None = None
