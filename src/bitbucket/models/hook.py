from __future__ import annotations

from bitbucket._time import BitbucketInstant
from bitbucket.models.base import BitbucketModel
from bitbucket.models.link import Links


class Webhook(BitbucketModel):
    uuid: str | None = None
    url: str | None = None
    description: str | None = None
    subject_type: str | None = None
    active: bool | None = None
    created_at: BitbucketInstant | None = None
    events: list[str] | None = None
    links: Links | None = None


class WebhookCreate(BitbucketModel):
    description: str
    url: str
    events: list[str]
    active: bool | None = None


class WebhookUpdate(BitbucketModel):
    description: str | None = None
    url: str | None = None
    events: list[str] | None = None
    active: bool | None = None
