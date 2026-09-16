from __future__ import annotations

from bitbucket._time import BitbucketInstant
from bitbucket.ids import CommitHash
from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.link import Links
from bitbucket.models.repository import Repository


class CommitRef(BitbucketModel):
    type: str | None = None
    hash: CommitHash | None = None
    links: Links | None = None


class AuthorRef(BitbucketModel):
    raw: str | None = None
    user: Account | None = None


class Commit(BitbucketModel):
    type: str | None = None
    hash: CommitHash | None = None
    date: BitbucketInstant | None = None
    message: str | None = None
    author: AuthorRef | None = None
    committer: AuthorRef | None = None
    parents: list[CommitRef] | None = None
    repository: Repository | None = None
    links: Links | None = None
