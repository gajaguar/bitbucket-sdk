from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict


class BitbucketModel(BaseModel):
    # No alias_generator: Bitbucket's wire names are already snake_case
    # (display_name, created_on, full_name). Only reserved-word fields
    # (Links.self_, CommentInline.from_) get an explicit Field(alias=...).
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
        frozen=True,
    )
