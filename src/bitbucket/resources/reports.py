from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.report import Report
from bitbucket.models.report import ReportAnnotation
from bitbucket.models.report import ReportAnnotationWrite
from bitbucket.models.report import ReportWrite
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    import builtins
    from collections.abc import Iterator
    from collections.abc import Sequence
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import JSONValue
    from bitbucket._transport import Transport


class AnnotationsResource:
    # Hand-written: `put` and `delete` take the caller's own id, and `put_many`
    # posts a JSON array, none of which NestedResource has a shape for.
    def __init__(self, transport: Transport, report_path: str) -> None:
        self._transport = transport
        self._path = f"{report_path}/annotations"

    # DELETE {path}/{annotation_id}
    def delete(self, annotation_id: str) -> None:
        self._transport.request("DELETE", f"{self._path}/{annotation_id}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET {path}/{annotation_id}
    def get(self, annotation_id: str) -> ReportAnnotation:
        data = self._transport.request("GET", f"{self._path}/{annotation_id}", kind=CqsKind.QUERY)
        return ReportAnnotation.model_validate(data)

    # GET {path} (auto-paginating)
    def list(self) -> Iterator[ReportAnnotation]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    def list_page(self, *, cursor: str | None = None) -> Page[ReportAnnotation]:
        data = self._transport.request("GET", cursor or self._path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), ReportAnnotation)

    # PUT {path}/{annotation_id}
    def put(self, annotation_id: str, payload: ReportAnnotationWrite) -> ReportAnnotation:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request(
            "PUT", f"{self._path}/{annotation_id}", kind=CqsKind.IDEMPOTENT_COMMAND, json=body
        )
        return ReportAnnotation.model_validate(data)

    # POST {path} (1 to 100 annotations, each keyed by its `external_id`)
    def put_many(self, payloads: Sequence[ReportAnnotationWrite]) -> builtins.list[ReportAnnotation]:
        body: JSONValue = [payload.model_dump(mode="json", by_alias=True, exclude_unset=True) for payload in payloads]
        data = self._transport.request("POST", self._path, kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
        return [ReportAnnotation.model_validate(item) for item in cast("list[dict[str, Any]]", data)]


class ReportsResource:
    # Hand-written for the same reason as AnnotationsResource.
    def __init__(self, transport: Transport, commit_path: str) -> None:
        self._transport = transport
        self._path = f"{commit_path}/reports"

    def annotations(self, report_id: str) -> AnnotationsResource:
        return AnnotationsResource(self._transport, f"{self._path}/{report_id}")

    # DELETE {path}/{report_id}
    def delete(self, report_id: str) -> None:
        self._transport.request("DELETE", f"{self._path}/{report_id}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET {path}/{report_id}
    def get(self, report_id: str) -> Report:
        data = self._transport.request("GET", f"{self._path}/{report_id}", kind=CqsKind.QUERY)
        return Report.model_validate(data)

    # GET {path} (auto-paginating)
    def list(self) -> Iterator[Report]:
        return paginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    def list_page(self, *, cursor: str | None = None) -> Page[Report]:
        data = self._transport.request("GET", cursor or self._path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), Report)

    # PUT {path}/{report_id}
    def put(self, report_id: str, payload: ReportWrite) -> Report:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = self._transport.request("PUT", f"{self._path}/{report_id}", kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
        return Report.model_validate(data)
