from __future__ import annotations

from bitbucket._time import BitbucketInstant
from bitbucket.models.base import BitbucketModel
from bitbucket.models.link import Link
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


class HookEvent(BitbucketModel):
    # `event` stays a plain string: Bitbucket adds events over time, and an enum
    # would reject a new one at validation.
    event: str | None = None
    category: str | None = None
    label: str | None = None
    description: str | None = None


class HookSubjectTypeLinks(BitbucketModel):
    events: Link | None = None


class HookSubjectType(BitbucketModel):
    links: HookSubjectTypeLinks | None = None


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
