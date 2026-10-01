from __future__ import annotations

from bitbucket._time import BitbucketInstant
from bitbucket.ids import Uuid
from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.link import Links


class SshKey(BitbucketModel):
    uuid: Uuid | None = None
    key: str | None = None
    comment: str | None = None
    label: str | None = None
    fingerprint: str | None = None
    owner: Account | None = None
    created_on: BitbucketInstant | None = None
    last_used: BitbucketInstant | None = None
    expires_on: BitbucketInstant | None = None
    type: str | None = None
    links: Links | None = None


class SshKeyCreate(BitbucketModel):
    key: str
    label: str | None = None


class SshKeyUpdate(BitbucketModel):
    # The spec's description says only `comment` can change, but its example
    # sends `label`, the user-defined name.
    label: str | None = None
