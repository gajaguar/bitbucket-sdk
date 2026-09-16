from __future__ import annotations

from bitbucket._time import BitbucketInstant
from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.branch import RefTarget
from bitbucket.models.branch import RefTargetSpec
from bitbucket.models.link import Links


class Tag(BitbucketModel):
    name: str | None = None
    target: RefTarget | None = None
    tagger: Account | None = None
    message: str | None = None
    date: BitbucketInstant | None = None
    type: str | None = None
    links: Links | None = None


class TagCreate(BitbucketModel):
    name: str
    target: RefTargetSpec
    message: str | None = None
