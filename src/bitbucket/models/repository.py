from __future__ import annotations

from enum import StrEnum

from bitbucket._time import BitbucketInstant
from bitbucket.ids import Uuid
from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.branch import Branch
from bitbucket.models.link import Links
from bitbucket.models.project import Project


class Scm(StrEnum):
    GIT = "git"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> Scm:
        del value
        return cls.UNKNOWN


class ForkPolicy(StrEnum):
    ALLOW_FORKS = "allow_forks"
    NO_PUBLIC_FORKS = "no_public_forks"
    NO_FORKS = "no_forks"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> ForkPolicy:
        del value
        return cls.UNKNOWN


class Repository(BitbucketModel):
    type: str | None = None
    uuid: Uuid | None = None
    full_name: str | None = None
    name: str | None = None
    description: str | None = None
    is_private: bool | None = None
    scm: Scm | None = None
    owner: Account | None = None
    project: Project | None = None
    mainbranch: Branch | None = None
    fork_policy: ForkPolicy | None = None
    has_issues: bool | None = None
    has_wiki: bool | None = None
    language: str | None = None
    size: int | None = None
    created_on: BitbucketInstant | None = None
    updated_on: BitbucketInstant | None = None
    links: Links | None = None
