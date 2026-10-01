from __future__ import annotations

from bitbucket._time import BitbucketInstant
from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.link import Links
from bitbucket.models.project import Project
from bitbucket.models.repository import Repository


class DeployKey(BitbucketModel):
    # `key` is the SSH public key, so it is a plain `str`, like `SshKey.key`. The
    # spec declares no `id`, but its examples and the `{key_id}` path use it, and
    # lists `added_on` where the examples show `created_on`.
    type: str | None = None
    id: int | None = None
    key: str | None = None
    repository: Repository | None = None
    comment: str | None = None
    label: str | None = None
    added_on: BitbucketInstant | None = None
    created_on: BitbucketInstant | None = None
    last_used: BitbucketInstant | None = None
    links: Links | None = None
    owner: Account | None = None


class ProjectDeployKey(BitbucketModel):
    type: str | None = None
    id: int | None = None
    key: str | None = None
    project: Project | None = None
    comment: str | None = None
    label: str | None = None
    added_on: BitbucketInstant | None = None
    created_on: BitbucketInstant | None = None
    last_used: BitbucketInstant | None = None
    links: Links | None = None
    created_by: Account | None = None


class DeployKeyCreate(BitbucketModel):
    key: str
    label: str | None = None


class DeployKeyUpdate(BitbucketModel):
    # The spec says the same key must be sent again; only the label changes.
    key: str
    label: str | None = None
