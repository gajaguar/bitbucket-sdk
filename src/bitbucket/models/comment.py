from __future__ import annotations

from pydantic import Field

from bitbucket._time import BitbucketInstant
from bitbucket.ids import CommentId
from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.link import Links
from bitbucket.models.pull_request import PullRequest
from bitbucket.models.pull_request import RenderedField


class CommentInline(BitbucketModel):
    # "from" is a Python keyword; access via comment.inline.from_.
    path: str | None = None
    to: int | None = None
    from_: int | None = Field(default=None, alias="from")


class CommentResolution(BitbucketModel):
    type: str | None = None
    user: Account | None = None
    created_on: BitbucketInstant | None = None


class Comment(BitbucketModel):
    type: str | None = None
    id: CommentId | None = None
    created_on: BitbucketInstant | None = None
    updated_on: BitbucketInstant | None = None
    content: RenderedField | None = None
    user: Account | None = None
    deleted: bool | None = None
    parent: Comment | None = None
    inline: CommentInline | None = None
    links: Links | None = None


class PullRequestComment(Comment):
    pullrequest: PullRequest | None = None
    resolution: CommentResolution | None = None
    pending: bool | None = None


class CommentInlineCreate(BitbucketModel):
    path: str
    to: int | None = None
    from_: int | None = Field(default=None, alias="from")


class CommentContentCreate(BitbucketModel):
    raw: str


class CommentParentRef(BitbucketModel):
    id: CommentId


class CommentCreate(BitbucketModel):
    content: CommentContentCreate
    inline: CommentInlineCreate | None = None
    parent: CommentParentRef | None = None


class CommentUpdate(BitbucketModel):
    content: CommentContentCreate
