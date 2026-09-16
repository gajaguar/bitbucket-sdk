from __future__ import annotations

from bitbucket.models.base import BitbucketModel
from bitbucket.models.branch import RefTarget
from bitbucket.models.link import Links


class TreeEntry(BitbucketModel):
    # "commit_file" or "commit_directory" — GET .../src/{commit}/{path} lists
    # a mix of both when `path` resolves to a directory.
    type: str | None = None
    path: str | None = None
    escaped_path: str | None = None
    size: int | None = None
    commit: RefTarget | None = None
    attributes: list[str] | None = None
    links: Links | None = None


class FileHistoryEntry(BitbucketModel):
    type: str | None = None
    path: str | None = None
    commit: RefTarget | None = None
