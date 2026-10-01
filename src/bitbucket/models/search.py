from __future__ import annotations

from bitbucket.models.base import BitbucketModel
from bitbucket.models.source import TreeEntry


class SearchSegment(BitbucketModel):
    text: str | None = None
    match: bool | None = None


class SearchLine(BitbucketModel):
    line: int | None = None
    segments: list[SearchSegment] | None = None


class SearchContentMatch(BitbucketModel):
    lines: list[SearchLine] | None = None


class CodeSearchResult(BitbucketModel):
    type: str | None = None
    content_match_count: int | None = None
    content_matches: list[SearchContentMatch] | None = None
    path_matches: list[SearchSegment] | None = None
    # The spec's `commit_file`, which TreeEntry already models.
    file: TreeEntry | None = None
