from __future__ import annotations

from bitbucket._time import BitbucketInstant
from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.branch import MergeStrategy
from bitbucket.models.branch import RefTarget
from bitbucket.models.link import Links


class Ref(BitbucketModel):
    # GET .../refs lists branches and tags together; this covers the union of
    # both shapes (`type` disambiguates which fields are meaningful).
    type: str | None = None
    name: str | None = None
    target: RefTarget | None = None
    merge_strategies: list[str] | None = None
    default_merge_strategy: MergeStrategy | None = None
    tagger: Account | None = None
    message: str | None = None
    date: BitbucketInstant | None = None
    links: Links | None = None
