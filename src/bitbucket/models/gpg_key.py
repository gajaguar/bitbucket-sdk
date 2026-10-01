from __future__ import annotations

from bitbucket._time import BitbucketInstant
from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.link import Links


class GpgKey(BitbucketModel):
    key: str | None = None
    key_id: str | None = None
    fingerprint: str | None = None
    parent_fingerprint: str | None = None
    name: str | None = None
    owner: Account | None = None
    created_on: BitbucketInstant | None = None
    added_on: BitbucketInstant | None = None
    expires_on: BitbucketInstant | None = None
    last_used: BitbucketInstant | None = None
    subkeys: list[GpgKey] | None = None
    type: str | None = None
    links: Links | None = None


class GpgKeyCreate(BitbucketModel):
    key: str
    name: str | None = None
