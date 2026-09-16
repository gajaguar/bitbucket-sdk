from __future__ import annotations

from bitbucket._time import BitbucketInstant
from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.comment import PullRequestComment
from bitbucket.models.pull_request import PullRequest


class ActivityUpdate(BitbucketModel):
    date: BitbucketInstant | None = None
    author: Account | None = None
    state: str | None = None
    title: str | None = None
    description: str | None = None


class ActivityApproval(BitbucketModel):
    date: BitbucketInstant | None = None
    user: Account | None = None


class Activity(BitbucketModel):
    # Bitbucket's activity feed is a polymorphic envelope: exactly one of these
    # keys is present per entry, matching which action produced it.
    update: ActivityUpdate | None = None
    approval: ActivityApproval | None = None
    changes_requested: ActivityApproval | None = None
    comment: PullRequestComment | None = None
    pull_request: PullRequest | None = None
