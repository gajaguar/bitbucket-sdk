from __future__ import annotations

from bitbucket.models.hook import Webhook
from bitbucket.models.hook import WebhookCreate
from bitbucket.models.hook import WebhookUpdate
from bitbucket.resources.base import DeletableResourceMixin
from bitbucket.resources.base import NestedResource


class HooksResource(NestedResource[Webhook, WebhookCreate, WebhookUpdate], DeletableResourceMixin):
    _path = "/hooks"
    _read_model = Webhook
