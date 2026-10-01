from __future__ import annotations

from bitbucket._time import BitbucketInstant
from bitbucket.ids import Uuid
from bitbucket.models.base import BitbucketModel
from bitbucket.models.link import Links


class Project(BitbucketModel):
    type: str | None = None
    uuid: Uuid | None = None
    key: str | None = None
    name: str | None = None
    description: str | None = None
    is_private: bool | None = None
    has_publicly_visible_repos: bool | None = None
    created_on: BitbucketInstant | None = None
    updated_on: BitbucketInstant | None = None
    links: Links | None = None


class ProjectCreate(BitbucketModel):
    key: str
    name: str
    description: str | None = None
    is_private: bool | None = None
    has_publicly_visible_repos: bool | None = None


class ProjectUpdate(BitbucketModel):
    key: str | None = None
    name: str | None = None
    description: str | None = None
    is_private: bool | None = None
    has_publicly_visible_repos: bool | None = None
