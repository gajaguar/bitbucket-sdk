from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import pytest
import respx
from httpx import Response

from bitbucket.errors import BitbucketAPIError
from bitbucket.errors import NotFoundError
from bitbucket.models import Pipeline
from bitbucket.models import PipelineCommitRef
from bitbucket.models import PipelineCommitTargetCreate
from bitbucket.models import PipelineCreate
from bitbucket.models import PipelineRefTargetCreate
from bitbucket.models import PipelineRefType
from bitbucket.models import PipelineResultName
from bitbucket.models import PipelineSelector
from bitbucket.models import PipelineSelectorType
from bitbucket.models import PipelineStageName
from bitbucket.models import PipelineStateName
from bitbucket.models import PipelineStepResultName
from bitbucket.models import PipelineStepStateName
from bitbucket.models import PipelineVariableCreate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient

PIPELINES: Final = f"{BASE_URL}/repositories/ws/repo/pipelines"


def _pipelines(client: BitbucketClient):
    return client.workspace("ws").repository("repo").pipelines


@respx.mock
def test_pipelines_list_follows_next_cursor_and_sends_filters(client: BitbucketClient) -> None:
    # Arrange
    next_url = f"{BASE_URL}/repositories/ws/repo/pipelines-page-2"
    first = respx.get(PIPELINES).mock(
        return_value=Response(200, json={"values": [{"uuid": "{a}", "build_number": 1}], "next": next_url}),
    )
    second = respx.get(next_url).mock(
        return_value=Response(200, json={"values": [{"uuid": "{b}", "build_number": 2}]}),
    )
    # Act
    pipelines = list(
        _pipelines(client).list(**{"target.branch": "main", "status": "COMPLETED", "sort": "-created_on"})
    )
    # Assert
    assert [pipeline.build_number for pipeline in pipelines] == [1, 2]
    assert dict(first.calls[0].request.url.params) == {
        "target.branch": "main",
        "status": "COMPLETED",
        "sort": "-created_on",
    }
    assert second.called


@respx.mock
def test_pipelines_list_page_requests_the_cursor_url_verbatim(client: BitbucketClient) -> None:
    # Arrange
    cursor = f"{BASE_URL}/repositories/ws/repo/pipelines-page-3?page=3&pagelen=5"
    route = respx.get(cursor).mock(return_value=Response(200, json={"values": [], "size": 0}))
    # Act
    page = _pipelines(client).list_page(cursor=cursor)
    # Assert
    assert route.called
    assert page.items == []
    assert page.next_cursor is None


@respx.mock
def test_pipelines_create_posts_a_ref_target_with_query_flags(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(PIPELINES).mock(return_value=Response(201, json={"uuid": "{p}", "build_number": 7}))
    payload = PipelineCreate(
        target=PipelineRefTargetCreate(
            ref_type=PipelineRefType.BRANCH,
            ref_name="main",
            selector=PipelineSelector(type=PipelineSelectorType.CUSTOM, pattern="deploy"),
        ),
        variables=[PipelineVariableCreate(key="ENV", value="prod", secured=False)],
    )
    # Act
    pipeline = _pipelines(client).create(payload, merge_defaults=True, target_branch_to_create="feature")
    # Assert
    request = route.calls[0].request
    assert json.loads(request.content) == {
        "target": {
            "type": "pipeline_ref_target",
            "ref_type": "branch",
            "ref_name": "main",
            "selector": {"type": "custom", "pattern": "deploy"},
        },
        "variables": [{"key": "ENV", "value": "prod", "secured": False}],
    }
    assert request.url.params["merge_defaults"] == "true"
    assert request.url.params["target_branch_to_create"] == "feature"
    assert pipeline.build_number == 7


@respx.mock
def test_pipelines_create_posts_a_commit_target_with_its_type(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(PIPELINES).mock(return_value=Response(201, json={"uuid": "{p}"}))
    payload = PipelineCreate(target=PipelineCommitTargetCreate(commit=PipelineCommitRef(hash="abc123")))
    # Act
    _pipelines(client).create(payload)
    # Assert
    request = route.calls[0].request
    assert json.loads(request.content) == {
        "target": {"type": "pipeline_commit_target", "commit": {"type": "commit", "hash": "abc123"}},
    }
    assert "merge_defaults" not in request.url.params


@respx.mock
def test_pipelines_create_raises_for_a_repository_without_pipelines(client: BitbucketClient) -> None:
    # Arrange
    respx.post(PIPELINES).mock(return_value=Response(400, json={"type": "error", "error": {"message": "disabled"}}))
    payload = PipelineCreate(target=PipelineRefTargetCreate(ref_type=PipelineRefType.TAG, ref_name="v1"))
    # Act
    with pytest.raises(BitbucketAPIError) as raised:
        _pipelines(client).create(payload)
    # Assert
    assert raised.value.status_code == 400


@respx.mock
def test_pipelines_get_parses_state_result_and_target(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{PIPELINES}/p1").mock(
        return_value=Response(
            200,
            json={
                "type": "pipeline",
                "uuid": "{p1}",
                "created_on": "2026-09-01T10:00:00.000Z",
                "target": {"type": "pipeline_ref_target", "ref_type": "branch", "ref_name": "main"},
                "trigger": {"type": "pipeline_trigger_manual"},
                "state": {
                    "type": "pipeline_state_completed",
                    "name": "COMPLETED",
                    "result": {"type": "pipeline_state_completed_error", "name": "ERROR", "error": {"key": "k"}},
                },
                "links": {"self": {"href": f"{PIPELINES}/p1"}, "steps": {"href": f"{PIPELINES}/p1/steps"}},
            },
        ),
    )
    # Act
    pipeline = _pipelines(client).get("p1")
    # Assert
    assert pipeline.target is not None
    assert pipeline.target.ref_type is PipelineRefType.BRANCH
    assert pipeline.state is not None
    assert pipeline.state.name is PipelineStateName.COMPLETED
    assert pipeline.state.result is not None
    assert pipeline.state.result.name is PipelineResultName.ERROR
    assert pipeline.state.result.error is not None
    assert pipeline.state.result.error.key == "k"
    assert pipeline.links is not None
    assert pipeline.links.steps is not None


def test_pipeline_states_fall_back_to_unknown_for_new_values() -> None:
    # Arrange
    payload = {"state": {"name": "SOMETHING_NEW", "stage": {"name": "BOOTING"}, "result": {"name": "WEIRD"}}}
    # Act
    pipeline = Pipeline.model_validate(payload)
    # Assert
    assert pipeline.state is not None
    assert pipeline.state.name is PipelineStateName.UNKNOWN
    assert pipeline.state.stage is not None
    assert pipeline.state.stage.name is PipelineStageName.UNKNOWN
    assert pipeline.state.result is not None
    assert pipeline.state.result.name is PipelineResultName.UNKNOWN


@respx.mock
def test_pipelines_get_raises_not_found_for_an_unknown_pipeline(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{PIPELINES}/missing").mock(return_value=Response(404, json={"type": "error"}))
    # Act
    with pytest.raises(NotFoundError) as raised:
        _pipelines(client).get("missing")
    # Assert
    assert raised.value.status_code == 404


@respx.mock
def test_pipelines_stop_posts_and_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{PIPELINES}/p1/stopPipeline").mock(return_value=Response(204))
    # Act
    result = _pipelines(client).stop("p1")
    # Assert
    assert route.called
    assert result is None


@respx.mock
def test_pipelines_stop_raises_for_a_completed_pipeline(client: BitbucketClient) -> None:
    # Arrange
    respx.post(f"{PIPELINES}/p1/stopPipeline").mock(return_value=Response(400, json={"type": "error"}))
    # Act
    with pytest.raises(BitbucketAPIError) as raised:
        _pipelines(client).stop("p1")
    # Assert
    assert raised.value.status_code == 400


@respx.mock
def test_pipelines_steps_follows_next_cursor(client: BitbucketClient) -> None:
    # Arrange
    next_url = f"{BASE_URL}/repositories/ws/repo/pipeline-steps-page-2"
    respx.get(f"{PIPELINES}/p1/steps").mock(
        return_value=Response(200, json={"values": [{"uuid": "{s1}"}], "next": next_url}),
    )
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{"uuid": "{s2}"}]}))
    # Act
    steps = list(_pipelines(client).steps("p1"))
    # Assert
    assert [step.uuid for step in steps] == ["{s1}", "{s2}"]


@respx.mock
def test_pipelines_step_parses_state_image_and_commands(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{PIPELINES}/p1/steps/s1").mock(
        return_value=Response(
            200,
            json={
                "uuid": "{s1}",
                "state": {
                    "name": "COMPLETED",
                    "result": {"name": "NOT_RUN"},
                },
                "image": {"name": "python:3", "username": "bot", "password": "hunter2"},
                "script_commands": [{"name": "test", "command": "pytest"}],
            },
        ),
    )
    # Act
    step = _pipelines(client).step("p1", "s1")
    # Assert
    assert step.state is not None
    assert step.state.name is PipelineStepStateName.COMPLETED
    assert step.state.result is not None
    assert step.state.result.name is PipelineStepResultName.NOT_RUN
    assert step.script_commands is not None
    assert step.script_commands[0].command == "pytest"
    assert step.image is not None
    assert step.image.password is not None
    assert step.image.password.get_secret_value() == "hunter2"
    assert "hunter2" not in repr(step)


@respx.mock
def test_pipelines_step_log_returns_bytes_without_a_range_by_default(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{PIPELINES}/p1/steps/s1/log").mock(return_value=Response(200, content=b"line 1\nline 2\n"))
    # Act
    log = _pipelines(client).step_log("p1", "s1")
    # Assert
    assert log == b"line 1\nline 2\n"
    assert "Range" not in route.calls[0].request.headers


@respx.mock
def test_pipelines_step_log_sends_a_range_header(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{PIPELINES}/p1/steps/s1/log").mock(return_value=Response(206, content=b"line"))
    # Act
    log = _pipelines(client).step_log("p1", "s1", start=10, end=19)
    # Assert
    assert log == b"line"
    assert route.calls[0].request.headers["Range"] == "bytes=10-19"


@respx.mock
def test_pipelines_step_log_sends_an_open_ended_range(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{PIPELINES}/p1/steps/s1/log").mock(return_value=Response(206, content=b"tail"))
    # Act
    _pipelines(client).step_log("p1", "s1", start=100)
    # Assert
    assert route.calls[0].request.headers["Range"] == "bytes=100-"


@respx.mock
def test_pipelines_step_log_follows_the_redirect_to_long_term_storage(client: BitbucketClient) -> None:
    # Arrange
    storage_url = "https://storage.example.com/logs/s1"
    respx.get(f"{PIPELINES}/p1/steps/s1/log").mock(return_value=Response(307, headers={"Location": storage_url}))
    storage = respx.get(storage_url).mock(return_value=Response(200, content=b"archived log"))
    # Act
    log = _pipelines(client).step_log("p1", "s1")
    # Assert
    assert log == b"archived log"
    assert "Authorization" not in storage.calls[0].request.headers


@respx.mock
def test_pipelines_step_log_raises_for_an_unsatisfiable_range(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{PIPELINES}/p1/steps/s1/log").mock(return_value=Response(416, content=b"range"))
    # Act
    with pytest.raises(BitbucketAPIError) as raised:
        _pipelines(client).step_log("p1", "s1", start=999999)
    # Assert
    assert raised.value.status_code == 416


@respx.mock
def test_pipelines_container_log_follows_the_redirect(client: BitbucketClient) -> None:
    # Arrange
    storage_url = "https://storage.example.com/logs/c1"
    respx.get(f"{PIPELINES}/p1/steps/s1/logs/c1").mock(return_value=Response(307, headers={"Location": storage_url}))
    respx.get(storage_url).mock(return_value=Response(200, content=b"container log"))
    # Act
    log = _pipelines(client).container_log("p1", "s1", "c1")
    # Assert
    assert log == b"container log"


@respx.mock
def test_pipelines_test_reports_return_the_raw_json(client: BitbucketClient) -> None:
    # Arrange
    summary = {"total": 3, "failed": 1}
    respx.get(f"{PIPELINES}/p1/steps/s1/test_reports").mock(return_value=Response(200, json=summary))
    # Act
    reports = _pipelines(client).test_reports("p1", "s1")
    # Assert
    assert reports == summary


@respx.mock
def test_pipelines_test_cases_return_the_raw_json(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{PIPELINES}/p1/steps/s1/test_reports/test_cases").mock(
        return_value=Response(200, json={"values": [{"uuid": "{t1}"}]}),
    )
    # Act
    cases = _pipelines(client).test_cases("p1", "s1")
    # Assert
    assert route.called
    assert cases == {"values": [{"uuid": "{t1}"}]}


@respx.mock
def test_pipelines_test_case_reasons_return_the_raw_json(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{PIPELINES}/p1/steps/s1/test_reports/test_cases/t1/test_case_reasons").mock(
        return_value=Response(200, json={"values": [{"message": "boom"}]}),
    )
    # Act
    reasons = _pipelines(client).test_case_reasons("p1", "s1", "t1")
    # Assert
    assert route.called
    assert reasons == {"values": [{"message": "boom"}]}
