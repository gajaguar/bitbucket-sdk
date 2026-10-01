from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import paginate
from bitbucket.models.pipeline import Pipeline
from bitbucket.models.pipeline import PipelineCreate
from bitbucket.models.pipeline import PipelineStep
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import JSONValue
    from bitbucket._transport import Transport


def range_header(start: int | None, end: int | None) -> dict[str, str] | None:
    if start is None and end is None:
        return None
    last = "" if end is None else str(end)
    return {"Range": f"bytes={start or 0}-{last}"}


class PipelinesResource:
    # Hand-written: create takes query parameters, the step and test-report
    # paths nest three ids deep, and the logs are bytes — none of which fit
    # NestedResource's {path}/{id} shape.
    def __init__(self, transport: Transport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/pipelines"

    # GET {path}/{pipeline_uuid}/steps/{step_uuid}/logs/{log_uuid}
    def container_log(self, pipeline_uuid: object, step_uuid: object, log_uuid: object) -> bytes:
        # Once the step is done Bitbucket answers 307 to long-term storage, so the redirect is followed.
        path = f"{self._path}/{pipeline_uuid}/steps/{step_uuid}/logs/{log_uuid}"
        return self._transport.request_bytes("GET", path, kind=CqsKind.QUERY, follow_redirects=True)

    # POST {path}
    def create(
        self,
        payload: PipelineCreate,
        *,
        merge_defaults: bool | None = None,
        target_branch_to_create: str | None = None,
    ) -> Pipeline:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        params = {"merge_defaults": merge_defaults, "target_branch_to_create": target_branch_to_create}
        data = self._transport.request(
            "POST", self._path, kind=CqsKind.NON_IDEMPOTENT_COMMAND, params=params, json=body
        )
        return Pipeline.model_validate(data)

    # GET {path}/{pipeline_uuid}
    def get(self, pipeline_uuid: object) -> Pipeline:
        data = self._transport.request("GET", f"{self._path}/{pipeline_uuid}", kind=CqsKind.QUERY)
        return Pipeline.model_validate(data)

    # GET {path} (auto-paginating) — filters use the spec's names, e.g. **{"target.branch": "main"}
    def list(self, **params: str | float | bool) -> Iterator[Pipeline]:
        return paginate(lambda cursor: self.list_page(cursor=cursor, **params))

    # GET {path}
    def list_page(self, *, cursor: str | None = None, **params: str | float | bool) -> Page[Pipeline]:
        if cursor:
            data = self._transport.request("GET", cursor, kind=CqsKind.QUERY)
        else:
            data = self._transport.request("GET", self._path, kind=CqsKind.QUERY, params=params or None)
        return page_from_payload(cast("dict[str, Any]", data), Pipeline)

    # GET {path}/{pipeline_uuid}/steps/{step_uuid}
    def step(self, pipeline_uuid: object, step_uuid: object) -> PipelineStep:
        data = self._transport.request("GET", f"{self._path}/{pipeline_uuid}/steps/{step_uuid}", kind=CqsKind.QUERY)
        return PipelineStep.model_validate(data)

    # GET {path}/{pipeline_uuid}/steps/{step_uuid}/log
    def step_log(
        self,
        pipeline_uuid: object,
        step_uuid: object,
        *,
        start: int | None = None,
        end: int | None = None,
    ) -> bytes:
        # `start`/`end` become a `Range: bytes=start-end` header; the spec asks for
        # range requests because step logs can be very large. A finished step's
        # log is a 307 to long-term storage, which is followed.
        path = f"{self._path}/{pipeline_uuid}/steps/{step_uuid}/log"
        return self._transport.request_bytes(
            "GET", path, kind=CqsKind.QUERY, headers=range_header(start, end), follow_redirects=True
        )

    # GET {path}/{pipeline_uuid}/steps (auto-paginating)
    def steps(self, pipeline_uuid: object) -> Iterator[PipelineStep]:
        return paginate(lambda cursor: self.steps_page(pipeline_uuid, cursor=cursor))

    # GET {path}/{pipeline_uuid}/steps
    def steps_page(self, pipeline_uuid: object, *, cursor: str | None = None) -> Page[PipelineStep]:
        data = self._transport.request("GET", cursor or f"{self._path}/{pipeline_uuid}/steps", kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), PipelineStep)

    # POST {path}/{pipeline_uuid}/stopPipeline
    def stop(self, pipeline_uuid: object) -> None:
        # Idempotent: a repeat only answers 400 "already completed", with no second effect.
        path = f"{self._path}/{pipeline_uuid}/stopPipeline"
        self._transport.request("POST", path, kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET {path}/{pipeline_uuid}/steps/{step_uuid}/test_reports/test_cases
    def test_cases(self, pipeline_uuid: object, step_uuid: object) -> JSONValue:
        # The spec gives no schema for the test-report endpoints, so the JSON is returned as is.
        path = f"{self._path}/{pipeline_uuid}/steps/{step_uuid}/test_reports/test_cases"
        return self._transport.request("GET", path, kind=CqsKind.QUERY)

    # GET {path}/{pipeline_uuid}/steps/{step_uuid}/test_reports/test_cases/{test_case_uuid}/test_case_reasons
    def test_case_reasons(self, pipeline_uuid: object, step_uuid: object, test_case_uuid: object) -> JSONValue:
        path = f"{self._path}/{pipeline_uuid}/steps/{step_uuid}/test_reports/test_cases/{test_case_uuid}"
        return self._transport.request("GET", f"{path}/test_case_reasons", kind=CqsKind.QUERY)

    # GET {path}/{pipeline_uuid}/steps/{step_uuid}/test_reports
    def test_reports(self, pipeline_uuid: object, step_uuid: object) -> JSONValue:
        path = f"{self._path}/{pipeline_uuid}/steps/{step_uuid}/test_reports"
        return self._transport.request("GET", path, kind=CqsKind.QUERY)
