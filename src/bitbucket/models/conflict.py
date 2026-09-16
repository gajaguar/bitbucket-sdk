from __future__ import annotations

from bitbucket.models.base import BitbucketModel


class FileConflict(BitbucketModel):
    path: str | None = None
    type: str | None = None
