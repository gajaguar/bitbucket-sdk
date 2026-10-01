from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.hook import HookEvent
from bitbucket.models.hook import HookSubjectType
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import Transport


class HookEventsResource:
    # Root-level catalogue of what a webhook can subscribe to, not workspace- or
    # repo-scoped — hand-written per the over-abstraction guard in docs/TECH_SPEC.md.
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    # GET /hook_events
    def subject_types(self) -> dict[str, HookSubjectType]:
        data = self._transport.request("GET", "/hook_events", kind=CqsKind.QUERY)
        return {name: HookSubjectType.model_validate(item) for name, item in cast("dict[str, Any]", data).items()}

    # GET .../hook_events/{subject_type} (auto-paginating)
    def list(self, subject_type: str) -> Iterator[HookEvent]:
        return paginate(lambda cursor: self.list_page(subject_type, cursor=cursor))

    # GET .../hook_events/{subject_type}
    def list_page(self, subject_type: str, *, cursor: str | None = None) -> Page[HookEvent]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", f"/hook_events/{subject_type}", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), HookEvent)
