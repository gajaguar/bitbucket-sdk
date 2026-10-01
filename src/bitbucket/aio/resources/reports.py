from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.models.report import Report
from bitbucket.models.report import ReportAnnotation
from bitbucket.models.report import ReportAnnotationWrite
from bitbucket.models.report import ReportWrite
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    import builtins
    from collections.abc import AsyncIterator
    from collections.abc import Sequence
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import JSONValue
    from bitbucket.aio._transport import AsyncTransport


class AsyncAnnotationsResource:
    # Hand-written: `put` and `delete` take the caller's own id, and `put_many`
    # posts a JSON array, none of which NestedResource has a shape for.
    def __init__(self, transport: AsyncTransport, report_path: str) -> None:
        self._transport = transport
        self._path = f"{report_path}/annotations"

    # DELETE {path}/{annotation_id}
    async def delete(self, annotation_id: str) -> None:
        await self._transport.request("DELETE", f"{self._path}/{annotation_id}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET {path}/{annotation_id}
    async def get(self, annotation_id: str) -> ReportAnnotation:
        data = await self._transport.request("GET", f"{self._path}/{annotation_id}", kind=CqsKind.QUERY)
        return ReportAnnotation.model_validate(data)

    # GET {path} (auto-paginating)
    def list(self) -> AsyncIterator[ReportAnnotation]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    async def list_page(self, *, cursor: str | None = None) -> Page[ReportAnnotation]:
        data = await self._transport.request("GET", cursor or self._path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), ReportAnnotation)

    # PUT {path}/{annotation_id}
    async def put(self, annotation_id: str, payload: ReportAnnotationWrite) -> ReportAnnotation:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request(
            "PUT", f"{self._path}/{annotation_id}", kind=CqsKind.IDEMPOTENT_COMMAND, json=body
        )
        return ReportAnnotation.model_validate(data)

    # POST {path} (1 to 100 annotations, each keyed by its `external_id`)
    async def put_many(self, payloads: Sequence[ReportAnnotationWrite]) -> builtins.list[ReportAnnotation]:
        body: JSONValue = [payload.model_dump(mode="json", by_alias=True, exclude_unset=True) for payload in payloads]
        data = await self._transport.request("POST", self._path, kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
        return [ReportAnnotation.model_validate(item) for item in cast("list[dict[str, Any]]", data)]


class AsyncReportsResource:
    # Hand-written for the same reason as AsyncAnnotationsResource.
    def __init__(self, transport: AsyncTransport, commit_path: str) -> None:
        self._transport = transport
        self._path = f"{commit_path}/reports"

    def annotations(self, report_id: str) -> AsyncAnnotationsResource:
        return AsyncAnnotationsResource(self._transport, f"{self._path}/{report_id}")

    # DELETE {path}/{report_id}
    async def delete(self, report_id: str) -> None:
        await self._transport.request("DELETE", f"{self._path}/{report_id}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET {path}/{report_id}
    async def get(self, report_id: str) -> Report:
        data = await self._transport.request("GET", f"{self._path}/{report_id}", kind=CqsKind.QUERY)
        return Report.model_validate(data)

    # GET {path} (auto-paginating)
    def list(self) -> AsyncIterator[Report]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    async def list_page(self, *, cursor: str | None = None) -> Page[Report]:
        data = await self._transport.request("GET", cursor or self._path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Report)

    # PUT {path}/{report_id}
    async def put(self, report_id: str, payload: ReportWrite) -> Report:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request(
            "PUT", f"{self._path}/{report_id}", kind=CqsKind.IDEMPOTENT_COMMAND, json=body
        )
        return Report.model_validate(data)
