from __future__ import annotations

from bitbucket.models.base import BitbucketModel
from bitbucket.models.link import Links


class UserEmail(BitbucketModel):
    # The spec declares no success schema for the email endpoints; this is the
    # shape their descriptions document.
    type: str | None = None
    email: str | None = None
    is_primary: bool | None = None
    is_confirmed: bool | None = None
    links: Links | None = None
