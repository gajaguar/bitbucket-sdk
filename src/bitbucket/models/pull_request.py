from __future__ import annotations

from enum import StrEnum
from typing import Literal

from bitbucket._time import BitbucketInstant
from bitbucket.ids import PullRequestId
from bitbucket.ids import Uuid
from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.branch import Branch
from bitbucket.models.commit import CommitRef
from bitbucket.models.link import Links
from bitbucket.models.repository import Repository

type PullRequestState = Literal[  # pylint: disable=app-module-const-naming
    "OPEN", "DRAFT", "QUEUED", "MERGED", "DECLINED", "SUPERSEDED"
]


class Markup(StrEnum):
    MARKDOWN = "markdown"
    CREOLE = "creole"
    PLAINTEXT = "plaintext"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> Markup:
        del value
        return cls.UNKNOWN


class ParticipantRole(StrEnum):
    PARTICIPANT = "PARTICIPANT"
    REVIEWER = "REVIEWER"
    AUTHOR = "AUTHOR"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> ParticipantRole:
        del value
        return cls.UNKNOWN


class ParticipantState(StrEnum):
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> ParticipantState:
        del value
        return cls.UNKNOWN


class RenderedField(BitbucketModel):
    raw: str | None = None
    markup: Markup | None = None
    html: str | None = None
    type: str | None = None


class PullRequestRendered(BitbucketModel):
    title: RenderedField | None = None
    description: RenderedField | None = None
    reason: RenderedField | None = None


class PullRequestEndpoint(BitbucketModel):
    repository: Repository | None = None
    branch: Branch | None = None
    commit: CommitRef | None = None


class Participant(BitbucketModel):
    type: str | None = None
    user: Account | None = None
    role: ParticipantRole | None = None
    approved: bool | None = None
    state: ParticipantState | None = None
    participated_on: BitbucketInstant | None = None


class PullRequest(BitbucketModel):
    type: str | None = None
    id: PullRequestId | None = None
    title: str | None = None
    description: str | None = None
    state: PullRequestState | None = None
    draft: bool | None = None
    queued: bool | None = None
    mergeable: bool | None = None
    close_source_branch: bool | None = None
    closed_by: Account | None = None
    reason: str | None = None
    author: Account | None = None
    source: PullRequestEndpoint | None = None
    destination: PullRequestEndpoint | None = None
    merge_commit: CommitRef | None = None
    comment_count: int | None = None
    task_count: int | None = None
    created_on: BitbucketInstant | None = None
    updated_on: BitbucketInstant | None = None
    reviewers: list[Account] | None = None
    participants: list[Participant] | None = None
    rendered: PullRequestRendered | None = None
    summary: RenderedField | None = None
    links: Links | None = None


class BranchSpec(BitbucketModel):
    # Write-side branch reference: Bitbucket accepts {"branch": {"name": "..."}}
    # (plus an optional "repository" for cross-repo destinations), not the full
    # read-side Branch/Repository shape.
    name: str


class RepositorySpec(BitbucketModel):
    full_name: str


class EndpointSpec(BitbucketModel):
    branch: BranchSpec
    repository: RepositorySpec | None = None


class ReviewerSpec(BitbucketModel):
    uuid: Uuid


class PullRequestCreate(BitbucketModel):
    title: str
    source: EndpointSpec
    destination: EndpointSpec | None = None
    description: str | None = None
    reviewers: list[ReviewerSpec] | None = None
    close_source_branch: bool | None = None


class PullRequestUpdate(BitbucketModel):
    title: str | None = None
    description: str | None = None
    reviewers: list[ReviewerSpec] | None = None
    destination: EndpointSpec | None = None
