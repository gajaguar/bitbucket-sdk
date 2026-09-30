from __future__ import annotations

from bitbucket.aio.resources.base import AsyncDeletableResourceMixin
from bitbucket.aio.resources.base import AsyncNestedResource
from bitbucket.models.hook import Webhook
from bitbucket.models.hook import WebhookCreate
from bitbucket.models.hook import WebhookUpdate


class AsyncHooksResource(
    AsyncNestedResource[Webhook, WebhookCreate, WebhookUpdate],
    AsyncDeletableResourceMixin,
):
    _path = "/hooks"
    _read_model = Webhook
