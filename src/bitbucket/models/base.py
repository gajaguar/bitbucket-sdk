from __future__ import annotations

from typing import Annotated
from typing import Self

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import PlainSerializer
from pydantic import SecretStr
from pydantic import model_validator


class BitbucketModel(BaseModel):
    # No alias_generator: Bitbucket's wire names are already snake_case
    # (display_name, created_on, full_name). Only reserved-word fields
    # (Links.self_, CommentInline.from_) get an explicit Field(alias=...).
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
        frozen=True,
    )


def _reveal_secret(value: SecretStr) -> str:
    return value.get_secret_value()


# Write models hold secrets as SecretStr so repr and logs mask them; the
# request body is the one place the real value must go out.
WriteSecret = Annotated[SecretStr, PlainSerializer(_reveal_secret, return_type=str, when_used="json")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


class TypedWriteModel(BitbucketModel):
    # The write helpers dump with exclude_unset, which would drop a defaulted
    # `type`; the discriminator must always reach the wire.
    @model_validator(mode="after")
    def _mark_type_set(self) -> Self:
        self.model_fields_set.add("type")
        return self
