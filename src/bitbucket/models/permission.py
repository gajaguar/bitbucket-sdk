from __future__ import annotations

from enum import StrEnum

from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.project import Project


class PermissionLevel(StrEnum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> PermissionLevel:
        del value
        return cls.UNKNOWN


class GroupRef(BitbucketModel):
    slug: str | None = None
    name: str | None = None


class GroupPermission(BitbucketModel):
    type: str | None = None
    permission: PermissionLevel | None = None
    group: GroupRef | None = None


class GroupPermissionUpdate(BitbucketModel):
    permission: PermissionLevel


class UserPermission(BitbucketModel):
    type: str | None = None
    permission: PermissionLevel | None = None
    user: Account | None = None


class UserPermissionUpdate(BitbucketModel):
    permission: PermissionLevel


class RepositoryOverrideSettings(BitbucketModel):
    branching_model: bool | None = None
    branch_restrictions: bool | None = None
    default_merge_strategy: bool | None = None


class RepositoryInheritanceState(BitbucketModel):
    type: str
    override_settings: RepositoryOverrideSettings | None = None


class ProjectPermissionLevel(StrEnum):
    READ = "read"
    WRITE = "write"
    CREATE_REPO = "create-repo"
    ADMIN = "admin"
    NONE = "none"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> ProjectPermissionLevel:
        del value
        return cls.UNKNOWN


class ProjectGroupPermission(BitbucketModel):
    type: str | None = None
    permission: ProjectPermissionLevel | None = None
    group: GroupRef | None = None
    project: Project | None = None


class ProjectUserPermission(BitbucketModel):
    type: str | None = None
    permission: ProjectPermissionLevel | None = None
    user: Account | None = None
    project: Project | None = None


class ProjectPermissionUpdate(BitbucketModel):
    permission: ProjectPermissionLevel
