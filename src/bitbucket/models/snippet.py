from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator

from bitbucket._time import BitbucketInstant
from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.comment import Comment
from bitbucket.models.comment import CommentContentCreate
from bitbucket.models.comment import CommentParentRef
from bitbucket.models.commit import AuthorRef
from bitbucket.models.commit import CommitRef
from bitbucket.models.link import Links
from bitbucket.models.pull_request import RenderedField


class SnippetScm(StrEnum):
    GIT = "git"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> SnippetScm:
        del value
        return cls.UNKNOWN


class SnippetRole(StrEnum):
    OWNER = "owner"
    CONTRIBUTOR = "contributor"
    MEMBER = "member"


class SnippetFile(BitbucketModel):
    links: Links | None = None


class Snippet(BitbucketModel):
    # `links` and `files` are not in the spec's `snippet` schema; they come from the
    # sample responses in the operation descriptions. The schema types `id` as an
    # integer, but the samples and the `{encoded_id}` path use a short string.
    type: str | None = None
    id: str | None = None
    title: str | None = None
    scm: SnippetScm | None = None
    created_on: BitbucketInstant | None = None
    updated_on: BitbucketInstant | None = None
    owner: Account | None = None
    creator: Account | None = None
    is_private: bool | None = None
    links: Links | None = None
    files: dict[str, SnippetFile] | None = None

    @field_validator("id", mode="before")
    @classmethod
    def _id_as_text(cls, value: object) -> object:
        return str(value) if isinstance(value, int) else value


class SnippetComment(Comment):
    snippet: Snippet | None = None


class SnippetCommit(BitbucketModel):
    # The spec's `snippet_commit` is `base_commit` plus `links` and `snippet`.
    type: str | None = None
    hash: str | None = None
    date: BitbucketInstant | None = None
    author: AuthorRef | None = None
    committer: AuthorRef | None = None
    message: str | None = None
    summary: RenderedField | None = None
    parents: list[CommitRef] | None = None
    links: Links | None = None
    snippet: Snippet | None = None


class SnippetCreate(BitbucketModel):
    title: str | None = None
    is_private: bool | None = None
    scm: SnippetScm | None = None


class SnippetUpdate(BitbucketModel):
    title: str | None = None
    is_private: bool | None = None


class SnippetCommentCreate(BitbucketModel):
    content: CommentContentCreate
    parent: CommentParentRef | None = None
