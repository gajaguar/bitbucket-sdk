from __future__ import annotations

from bitbucket.models.base import BitbucketModel


class DiffStatEndpoint(BitbucketModel):
    type: str | None = None
    path: str | None = None
    escaped_path: str | None = None


class DiffStat(BitbucketModel):
    type: str | None = None
    status: str | None = None
    lines_added: int | None = None
    lines_removed: int | None = None
    old: DiffStatEndpoint | None = None
    new: DiffStatEndpoint | None = None
