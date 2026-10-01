from __future__ import annotations

from enum import StrEnum

from pydantic import SecretStr

from bitbucket._time import BitbucketInstant
from bitbucket.ids import Uuid
from bitbucket.models.base import BitbucketModel


class RunnerStatus(StrEnum):
    UNREGISTERED = "UNREGISTERED"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DISABLED = "DISABLED"
    ENABLED = "ENABLED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> RunnerStatus:
        del value
        return cls.UNKNOWN


class RunnerVersion(BitbucketModel):
    type: str | None = None
    version: str | None = None
    current: str | None = None


class RunnerState(BitbucketModel):
    type: str | None = None
    status: RunnerStatus | None = None
    version: RunnerVersion | None = None
    updated_on: BitbucketInstant | None = None
    cordoned: bool | None = None


class RunnerOAuthClient(BitbucketModel):
    type: str | None = None
    id: str | None = None
    secret: SecretStr | None = None
    token_endpoint: str | None = None
    audience: str | None = None


class Runner(BitbucketModel):
    type: str | None = None
    uuid: Uuid | None = None
    name: str | None = None
    labels: list[str] | None = None
    state: RunnerState | None = None
    created_on: BitbucketInstant | None = None
    updated_on: BitbucketInstant | None = None
    oauth_client: RunnerOAuthClient | None = None


class RunnerCreate(BitbucketModel):
    # The spec declares no request body for runner POST/PUT; these two fields
    # are the writable ones among the `pipeline_runner` properties.
    name: str | None = None
    labels: list[str] | None = None


class RunnerUpdate(BitbucketModel):
    name: str | None = None
    labels: list[str] | None = None
