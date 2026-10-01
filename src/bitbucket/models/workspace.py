from __future__ import annotations

from enum import StrEnum

from bitbucket._time import BitbucketInstant
from bitbucket.ids import Uuid
from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.link import Links


class WorkspaceForkingMode(StrEnum):
    ALLOW_FORKS = "allow_forks"
    INTERNAL_ONLY = "internal_only"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> WorkspaceForkingMode:
        del value
        return cls.UNKNOWN


class WorkspacePermissionLevel(StrEnum):
    OWNER = "owner"
    # Bitbucket is removing the collaborator role; it still parses while it lasts.
    COLLABORATOR = "collaborator"
    MEMBER = "member"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> WorkspacePermissionLevel:
        del value
        return cls.UNKNOWN


class Workspace(BitbucketModel):
    type: str | None = None
    uuid: Uuid | None = None
    name: str | None = None
    slug: str | None = None
    is_private: bool | None = None
    is_personal: bool | None = None
    is_privacy_enforced: bool | None = None
    forking_mode: WorkspaceForkingMode | None = None
    created_on: BitbucketInstant | None = None
    updated_on: BitbucketInstant | None = None
    links: Links | None = None


class WorkspaceMembership(BitbucketModel):
    type: str | None = None
    # The spec's schema omits these three, but the endpoint descriptions and
    # examples return them; the last two disappear once administration moves
    # to admin.atlassian.com, hence optional.
    permission: WorkspacePermissionLevel | None = None
    last_accessed: BitbucketInstant | None = None
    added_on: BitbucketInstant | None = None
    user: Account | None = None
    workspace: Workspace | None = None
    links: Links | None = None


class WorkspaceAccess(BitbucketModel):
    type: str | None = None
    administrator: bool | None = None
    workspace: Workspace | None = None
