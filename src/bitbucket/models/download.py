from __future__ import annotations

from bitbucket._time import BitbucketInstant
from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.link import Links


class Download(BitbucketModel):
    name: str | None = None
    size: int | None = None
    downloads: int | None = None
    created_on: BitbucketInstant | None = None
    user: Account | None = None
    links: Links | None = None
