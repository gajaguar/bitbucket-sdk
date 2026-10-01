from __future__ import annotations

from enum import StrEnum

from pydantic import Field
from pydantic import SecretStr

from bitbucket._time import BitbucketInstant
from bitbucket.ids import CommitHash
from bitbucket.ids import Uuid
from bitbucket.models.account import Account
from bitbucket.models.base import BitbucketModel
from bitbucket.models.base import TypedWriteModel
from bitbucket.models.commit import Commit
from bitbucket.models.link import Link
from bitbucket.models.pipeline_variable import PipelineVariable
from bitbucket.models.pipeline_variable import PipelineVariableCreate
from bitbucket.models.repository import Repository


class PipelineStateName(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> PipelineStateName:
        del value
        return cls.UNKNOWN


class PipelineStageName(StrEnum):
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> PipelineStageName:
        del value
        return cls.UNKNOWN


class PipelineResultName(StrEnum):
    ERROR = "ERROR"
    FAILED = "FAILED"
    STOPPED = "STOPPED"
    EXPIRED = "EXPIRED"
    SUCCESSFUL = "SUCCESSFUL"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> PipelineResultName:
        del value
        return cls.UNKNOWN


class PipelineStepStateName(StrEnum):
    PENDING = "PENDING"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> PipelineStepStateName:
        del value
        return cls.UNKNOWN


class PipelineStepResultName(StrEnum):
    ERROR = "ERROR"
    FAILED = "FAILED"
    STOPPED = "STOPPED"
    NOT_RUN = "NOT_RUN"
    EXPIRED = "EXPIRED"
    SUCCESSFUL = "SUCCESSFUL"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> PipelineStepResultName:
        del value
        return cls.UNKNOWN


class PipelineRefType(StrEnum):
    BRANCH = "branch"
    TAG = "tag"
    NAMED_BRANCH = "named_branch"
    BOOKMARK = "bookmark"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> PipelineRefType:
        del value
        return cls.UNKNOWN


class PipelineSelectorType(StrEnum):
    BRANCHES = "branches"
    TAGS = "tags"
    BOOKMARKS = "bookmarks"
    DEFAULT = "default"
    CUSTOM = "custom"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> PipelineSelectorType:
        del value
        return cls.UNKNOWN


class PipelineError(BitbucketModel):
    # Also the shape of `pipeline_step_error`: both carry a key and a message.
    key: str | None = None
    message: str | None = None


class PipelineSelector(BitbucketModel):
    type: PipelineSelectorType | None = None
    pattern: str | None = None


class PipelineTarget(BitbucketModel):
    # One model for `pipeline_ref_target` and `pipeline_commit_target`: the spec
    # makes the second a subset of the first, and `type` tells them apart.
    type: str | None = None
    ref_type: PipelineRefType | None = None
    ref_name: str | None = None
    commit: Commit | None = None
    selector: PipelineSelector | None = None


class PipelineTrigger(BitbucketModel):
    # `pipeline_trigger_push` and `pipeline_trigger_manual` add no properties.
    type: str | None = None


class PipelineStateStage(BitbucketModel):
    type: str | None = None
    name: PipelineStageName | None = None


class PipelineStateResult(BitbucketModel):
    type: str | None = None
    name: PipelineResultName | None = None
    error: PipelineError | None = None


class PipelineState(BitbucketModel):
    type: str | None = None
    name: PipelineStateName | None = None
    stage: PipelineStateStage | None = None
    result: PipelineStateResult | None = None


class PipelineStepResult(BitbucketModel):
    type: str | None = None
    name: PipelineStepResultName | None = None
    error: PipelineError | None = None


class PipelineStepState(BitbucketModel):
    type: str | None = None
    name: PipelineStepStateName | None = None
    result: PipelineStepResult | None = None


class PipelineImage(BitbucketModel):
    name: str | None = None
    username: str | None = None
    password: SecretStr | None = None
    email: str | None = None


class PipelineCommand(BitbucketModel):
    name: str | None = None
    command: str | None = None


class PipelineConfigurationSource(BitbucketModel):
    source: str | None = None
    uri: str | None = None


class PipelineLinks(BitbucketModel):
    # "self" is a Python keyword; access via links.self_.
    self_: Link | None = Field(default=None, alias="self")
    steps: Link | None = None


class Pipeline(BitbucketModel):
    type: str | None = None
    uuid: Uuid | None = None
    build_number: int | None = None
    creator: Account | None = None
    repository: Repository | None = None
    target: PipelineTarget | None = None
    trigger: PipelineTrigger | None = None
    state: PipelineState | None = None
    variables: list[PipelineVariable] | None = None
    created_on: BitbucketInstant | None = None
    completed_on: BitbucketInstant | None = None
    build_seconds_used: int | None = None
    configuration_sources: list[PipelineConfigurationSource] | None = None
    links: PipelineLinks | None = None


class PipelineStep(BitbucketModel):
    type: str | None = None
    uuid: Uuid | None = None
    started_on: BitbucketInstant | None = None
    completed_on: BitbucketInstant | None = None
    state: PipelineStepState | None = None
    image: PipelineImage | None = None
    setup_commands: list[PipelineCommand] | None = None
    script_commands: list[PipelineCommand] | None = None


class PipelineScheduleExecution(BitbucketModel):
    # `pipeline_schedule_execution_executed` carries a pipeline,
    # `..._errored` an error; `type` tells them apart.
    type: str | None = None
    pipeline: Pipeline | None = None
    error: PipelineError | None = None


class PipelineCommitRef(TypedWriteModel):
    type: str = "commit"
    hash: CommitHash


class PipelineRefTargetCreate(TypedWriteModel):
    type: str = "pipeline_ref_target"
    ref_type: PipelineRefType
    ref_name: str
    commit: PipelineCommitRef | None = None
    selector: PipelineSelector | None = None


class PipelineCommitTargetCreate(TypedWriteModel):
    type: str = "pipeline_commit_target"
    commit: PipelineCommitRef
    selector: PipelineSelector | None = None


class PipelineCreate(BitbucketModel):
    target: PipelineRefTargetCreate | PipelineCommitTargetCreate
    variables: list[PipelineVariableCreate] | None = None
