from __future__ import annotations

from pydantic import SecretStr

from bitbucket._time import BitbucketInstant
from bitbucket.ids import Uuid
from bitbucket.models.base import BitbucketModel
from bitbucket.models.base import TypedWriteModel
from bitbucket.models.base import WriteSecret
from bitbucket.models.pipeline import PipelineRefType
from bitbucket.models.pipeline import PipelineSelector
from bitbucket.models.pipeline import PipelineTarget
from bitbucket.models.repository import Repository


class PipelinesConfig(BitbucketModel):
    type: str | None = None
    enabled: bool | None = None
    repository: Repository | None = None


class PipelinesConfigUpdate(BitbucketModel):
    enabled: bool | None = None


class PipelineBuildNumber(BitbucketModel):
    type: str | None = None
    next: int | None = None


class PipelineBuildNumberUpdate(BitbucketModel):
    next: int


class PipelineSchedule(BitbucketModel):
    type: str | None = None
    uuid: Uuid | None = None
    enabled: bool | None = None
    target: PipelineTarget | None = None
    cron_pattern: str | None = None
    created_on: BitbucketInstant | None = None
    updated_on: BitbucketInstant | None = None


class PipelineScheduleTargetCreate(TypedWriteModel):
    type: str = "pipeline_ref_target"
    ref_type: PipelineRefType
    ref_name: str
    selector: PipelineSelector


class PipelineScheduleCreate(BitbucketModel):
    target: PipelineScheduleTargetCreate
    cron_pattern: str
    enabled: bool | None = None


class PipelineScheduleUpdate(BitbucketModel):
    enabled: bool | None = None


class PipelineSshKeyPair(BitbucketModel):
    # Bitbucket returns the public key only; `private_key` exists for the PUT.
    type: str | None = None
    private_key: SecretStr | None = None
    public_key: str | None = None


class PipelineSshKeyPairUpdate(BitbucketModel):
    private_key: WriteSecret | None = None
    public_key: str | None = None


class PipelineSshPublicKey(BitbucketModel):
    type: str | None = None
    key_type: str | None = None
    key: str | None = None
    md5_fingerprint: str | None = None
    sha256_fingerprint: str | None = None


class PipelineKnownHost(BitbucketModel):
    type: str | None = None
    uuid: Uuid | None = None
    hostname: str | None = None
    public_key: PipelineSshPublicKey | None = None


class PipelineKnownHostCreate(BitbucketModel):
    hostname: str
    public_key: PipelineSshPublicKey | None = None


class PipelineKnownHostUpdate(BitbucketModel):
    hostname: str | None = None
    public_key: PipelineSshPublicKey | None = None


class PipelineCache(BitbucketModel):
    type: str | None = None
    uuid: Uuid | None = None
    pipeline_uuid: Uuid | None = None
    step_uuid: Uuid | None = None
    name: str | None = None
    key_hash: str | None = None
    path: str | None = None
    file_size_bytes: int | None = None
    created_on: BitbucketInstant | None = None


class PipelineCacheContentUri(BitbucketModel):
    uri: str | None = None
