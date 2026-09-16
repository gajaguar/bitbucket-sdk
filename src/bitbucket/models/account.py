from __future__ import annotations

from enum import StrEnum
from typing import Literal

from bitbucket._time import BitbucketInstant
from bitbucket.ids import AccountId
from bitbucket.ids import Uuid
from bitbucket.models.base import BitbucketModel
from bitbucket.models.link import AccountLinks


class UserType(StrEnum):
    USER = "user"
    TEAM = "team"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> UserType:
        del value
        return cls.UNKNOWN


class Account(BitbucketModel):
    type: UserType | None = None
    uuid: Uuid | None = None
    display_name: str | None = None
    nickname: str | None = None
    account_id: AccountId | None = None
    created_on: BitbucketInstant | None = None
    links: AccountLinks | None = None


class DefaultReviewer(Account):
    reviewer_type: Literal["repository", "project"] | None = None
