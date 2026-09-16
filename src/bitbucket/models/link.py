from __future__ import annotations

from pydantic import Field

from bitbucket.models.base import BitbucketModel


class Link(BitbucketModel):
    href: str | None = None
    name: str | None = None


class Links(BitbucketModel):
    # "self" is a Python keyword; access via links.self_.
    self_: Link | None = Field(default=None, alias="self")
    html: Link | None = None
    avatar: Link | None = None
    code: Link | None = None
    commits: Link | None = None
    comments: Link | None = None
    approve: Link | None = None
    diff: Link | None = None
    diffstat: Link | None = None
    patch: Link | None = None
    activity: Link | None = None
    merge: Link | None = None
    decline: Link | None = None
    statuses: Link | None = None
    branches: Link | None = None
    tags: Link | None = None
    watchers: Link | None = None
    forks: Link | None = None
    downloads: Link | None = None
    issues: Link | None = None
    milestones: Link | None = None
    pullrequests: Link | None = None
    source: Link | None = None
    clone: Link | None = None


class AccountLinks(BitbucketModel):
    avatar: Link | None = None
    html: Link | None = None
    repositories: Link | None = None
    snippets: Link | None = None
