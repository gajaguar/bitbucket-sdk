from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import respx
from httpx import Response

from bitbucket.models import AnnotationSeverity
from bitbucket.models import ReportAnnotationWrite
from bitbucket.models import ReportData
from bitbucket.models import ReportDataType
from bitbucket.models import ReportResult
from bitbucket.models import ReportType
from bitbucket.models import ReportWrite
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.aio.client import AsyncBitbucketClient

REPORTS: Final = f"{BASE_URL}/repositories/ws/repo/commit/abc/reports"
REPORT_BODY: Final = {
    "uuid": "{r-1}",
    "title": "Scan",
    "report_type": "SECURITY",
    "result": "FAILED",
    "data": [{"title": "Safe?", "type": "BOOLEAN", "value": False}],
}
ANNOTATION_BODY: Final = {
    "uuid": "{a-1}",
    "external_id": "sys-1",
    "annotation_type": "VULNERABILITY",
    "severity": "HIGH",
    "line": 42,
}


def _reports(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").repository("repo").commits.reports("abc")


@respx.mock
async def test_reports_list_follows_the_next_link(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    next_url = f"{BASE_URL}/repositories/ws/repo/commit/abc/reports-page-2"
    respx.get(REPORTS).mock(return_value=Response(200, json={"values": [REPORT_BODY], "next": next_url}))
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{**REPORT_BODY, "uuid": "{r-2}"}]}))
    # Act
    result = [item async for item in _reports(aclient).list()]
    # Assert
    assert [report.uuid for report in result] == ["{r-1}", "{r-2}"]


@respx.mock
async def test_reports_get_parses_enums_and_data(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{REPORTS}/sys-1").mock(return_value=Response(200, json=REPORT_BODY))
    # Act
    report = await _reports(aclient).get("sys-1")
    # Assert
    assert report.report_type is ReportType.SECURITY
    assert report.result is ReportResult.FAILED
    assert report.data is not None
    assert report.data[0].type is ReportDataType.BOOLEAN
    assert report.data[0].value is False


@respx.mock
async def test_reports_get_maps_an_unlisted_result_to_unknown(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{REPORTS}/sys-1").mock(return_value=Response(200, json={"result": "BLOCKED"}))
    # Act
    report = await _reports(aclient).get("sys-1")
    # Assert
    assert report.result is ReportResult.UNKNOWN


@respx.mock
async def test_reports_put_sends_only_the_fields_that_were_set(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{REPORTS}/sys-1").mock(return_value=Response(200, json=REPORT_BODY))
    payload = ReportWrite(
        title="Scan",
        report_type=ReportType.SECURITY,
        data=[ReportData(type=ReportDataType.LINK, title="Docs", value={"text": "x", "href": "https://x"})],
    )
    # Act
    report = await _reports(aclient).put("sys-1", payload)
    # Assert
    assert json.loads(route.calls[0].request.content) == {
        "title": "Scan",
        "report_type": "SECURITY",
        "data": [{"type": "LINK", "title": "Docs", "value": {"text": "x", "href": "https://x"}}],
    }
    assert report.uuid == "{r-1}"


@respx.mock
async def test_reports_delete_sends_delete(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{REPORTS}/sys-1").mock(return_value=Response(204))
    # Act
    await _reports(aclient).delete("sys-1")
    # Assert
    assert route.called


@respx.mock
async def test_annotations_list_get_and_delete(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    base = f"{REPORTS}/sys-1/annotations"
    next_url = f"{BASE_URL}/repositories/ws/repo/commit/abc/annotations-page-2"
    respx.get(base).mock(return_value=Response(200, json={"values": [ANNOTATION_BODY], "next": next_url}))
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{**ANNOTATION_BODY, "uuid": "{a-2}"}]}))
    respx.get(f"{base}/sys-1").mock(return_value=Response(200, json=ANNOTATION_BODY))
    deleted = respx.delete(f"{base}/sys-1").mock(return_value=Response(204))
    annotations = _reports(aclient).annotations("sys-1")
    # Act
    listed = [item async for item in annotations.list()]
    fetched = await annotations.get("sys-1")
    await annotations.delete("sys-1")
    # Assert
    assert [annotation.uuid for annotation in listed] == ["{a-1}", "{a-2}"]
    assert fetched.severity is AnnotationSeverity.HIGH
    assert fetched.line == 42
    assert deleted.called


@respx.mock
async def test_annotations_put_sends_the_annotation(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{REPORTS}/sys-1/annotations/sys-1").mock(return_value=Response(200, json=ANNOTATION_BODY))
    payload = ReportAnnotationWrite(external_id="sys-1", path="src/a.py", line=42, severity=AnnotationSeverity.HIGH)
    # Act
    annotation = await _reports(aclient).annotations("sys-1").put("sys-1", payload)
    # Assert
    assert json.loads(route.calls[0].request.content) == {
        "external_id": "sys-1",
        "path": "src/a.py",
        "line": 42,
        "severity": "HIGH",
    }
    assert annotation.uuid == "{a-1}"


@respx.mock
async def test_annotations_put_many_posts_a_json_array_and_parses_the_array(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{REPORTS}/sys-1/annotations").mock(
        return_value=Response(200, json=[ANNOTATION_BODY, {**ANNOTATION_BODY, "uuid": "{a-2}"}])
    )
    payloads = [ReportAnnotationWrite(external_id="sys-1"), ReportAnnotationWrite(external_id="sys-2")]
    # Act
    result = await _reports(aclient).annotations("sys-1").put_many(payloads)
    # Assert
    assert json.loads(route.calls[0].request.content) == [{"external_id": "sys-1"}, {"external_id": "sys-2"}]
    assert [annotation.uuid for annotation in result] == ["{a-1}", "{a-2}"]
