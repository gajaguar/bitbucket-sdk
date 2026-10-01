from __future__ import annotations

from enum import StrEnum

from bitbucket._time import BitbucketInstant
from bitbucket.ids import Uuid
from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.base import TypedWriteModel
from bitbucket.models.commit import Commit


class DeploymentStateName(StrEnum):
    UNDEPLOYED = "UNDEPLOYED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> DeploymentStateName:
        del value
        return cls.UNKNOWN


class DeploymentStatusName(StrEnum):
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"
    STOPPED = "STOPPED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> DeploymentStatusName:
        del value
        return cls.UNKNOWN


class DeploymentStatus(BitbucketModel):
    # One model for the three `deployment_state_completed_status_*` subtypes:
    # they differ only in `name`.
    type: str | None = None
    name: DeploymentStatusName | None = None


class DeploymentState(BitbucketModel):
    # One model for `deployment_state_undeployed`, `..._in_progress` and
    # `..._completed`: `name` tells them apart, and each adds only a few fields.
    type: str | None = None
    name: DeploymentStateName | None = None
    trigger_url: str | None = None
    url: str | None = None
    deployer: Account | None = None
    status: DeploymentStatus | None = None
    start_date: BitbucketInstant | None = None
    completion_date: BitbucketInstant | None = None


class DeploymentRelease(BitbucketModel):
    type: str | None = None
    uuid: Uuid | None = None
    name: str | None = None
    url: str | None = None
    commit: Commit | None = None
    created_on: BitbucketInstant | None = None


class Environment(BitbucketModel):
    # The spec declares only `uuid` and `name`; the models accept extra fields.
    type: str | None = None
    uuid: Uuid | None = None
    name: str | None = None


class Deployment(BitbucketModel):
    type: str | None = None
    uuid: Uuid | None = None
    state: DeploymentState | None = None
    environment: Environment | None = None
    release: DeploymentRelease | None = None


class EnvironmentCreate(TypedWriteModel):
    type: str = "deployment_environment"
    name: str


class EnvironmentUpdate(BitbucketModel):
    # `POST .../changes` declares no request body; `name` is the one writable
    # field `deployment_environment` documents.
    name: str | None = None
