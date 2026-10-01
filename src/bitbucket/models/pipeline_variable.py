from __future__ import annotations

from pydantic import SecretStr

from bitbucket.ids import Uuid
from bitbucket.models.base import BitbucketModel
from bitbucket.models.base import WriteSecret


class PipelineVariable(BitbucketModel):
    # `value` is a SecretStr even for unsecured variables: Bitbucket leaves it
    # empty for a secured one, and masking the rest keeps repr safe either way.
    uuid: Uuid | None = None
    key: str | None = None
    value: SecretStr | None = None
    secured: bool | None = None


class PipelineVariableCreate(BitbucketModel):
    key: str
    value: WriteSecret
    secured: bool | None = None


class PipelineVariableUpdate(BitbucketModel):
    key: str | None = None
    value: WriteSecret | None = None
    secured: bool | None = None
