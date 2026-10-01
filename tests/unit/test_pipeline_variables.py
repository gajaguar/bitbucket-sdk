from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING
from typing import Final

import pytest
import respx
from httpx import Response

from bitbucket.errors import ConflictError
from bitbucket.errors import NotFoundError
from bitbucket.models import PipelineVariable
from bitbucket.models import PipelineVariableCreate
from bitbucket.models import PipelineVariableUpdate
from bitbucket.models import RunnerCreate
from bitbucket.models import RunnerStatus
from bitbucket.models import RunnerUpdate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitbucket.client import BitbucketClient
    from bitbucket.resources.pipeline_variables import PipelineVariablesResource
    from bitbucket.resources.runners import RunnersResource

# The spec spells the segment `pipelines_config` for repository, team and user
# scopes and `pipelines-config` for the workspace; each path is copied as is.
VARIABLE_SCOPES: Final[dict[str, tuple[Callable[[BitbucketClient], PipelineVariablesResource], str]]] = {
    "repository": (
        lambda client: client.workspace("ws").repository("repo").pipelines_config.variables,
        f"{BASE_URL}/repositories/ws/repo/pipelines_config/variables",
    ),
    "workspace": (
        lambda client: client.workspace("ws").pipelines_config.variables,
        f"{BASE_URL}/workspaces/ws/pipelines-config/variables",
    ),
    "team": (
        lambda client: client.teams("acme").pipelines_config.variables,
        f"{BASE_URL}/teams/acme/pipelines_config/variables",
    ),
    "user": (
        lambda client: client.users("bob").pipelines_config.variables,
        f"{BASE_URL}/users/bob/pipelines_config/variables",
    ),
}
RUNNER_SCOPES: Final[dict[str, tuple[Callable[[BitbucketClient], RunnersResource], str]]] = {
    "repository": (
        lambda client: client.workspace("ws").repository("repo").pipelines_config.runners,
        f"{BASE_URL}/repositories/ws/repo/pipelines-config/runners",
    ),
    "workspace": (
        lambda client: client.workspace("ws").pipelines_config.runners,
        f"{BASE_URL}/workspaces/ws/pipelines-config/runners",
    ),
}
VARIABLE_SCOPE: Final = pytest.mark.parametrize("scope", sorted(VARIABLE_SCOPES))
RUNNER_SCOPE: Final = pytest.mark.parametrize("scope", sorted(RUNNER_SCOPES))


@VARIABLE_SCOPE
@respx.mock
def test_variables_list_follows_next_cursor(client: BitbucketClient, scope: str) -> None:
    # Arrange
    accessor, path = VARIABLE_SCOPES[scope]
    next_url = f"{BASE_URL}/variables-page-2/{scope}"
    respx.get(path).mock(return_value=Response(200, json={"values": [{"key": "A"}], "next": next_url}))
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{"key": "B"}]}))
    # Act
    variables = list(accessor(client).list())
    # Assert
    assert [variable.key for variable in variables] == ["A", "B"]


@VARIABLE_SCOPE
@respx.mock
def test_variables_create_posts_the_real_value_and_hides_it_in_repr(client: BitbucketClient, scope: str) -> None:
    # Arrange
    accessor, path = VARIABLE_SCOPES[scope]
    route = respx.post(path).mock(return_value=Response(201, json={"uuid": "{v1}", "key": "TOKEN", "secured": True}))
    payload = PipelineVariableCreate(key="TOKEN", value="s3cr3t-value", secured=True)
    # Act
    variable = accessor(client).create(payload)
    # Assert
    assert json.loads(route.calls[0].request.content) == {"key": "TOKEN", "value": "s3cr3t-value", "secured": True}
    assert variable.uuid == "{v1}"
    assert "s3cr3t-value" not in repr(payload)
    assert "s3cr3t-value" not in str(payload)
    assert "s3cr3t-value" not in repr(variable)


@VARIABLE_SCOPE
@respx.mock
def test_variables_get_returns_the_variable(client: BitbucketClient, scope: str) -> None:
    # Arrange
    accessor, path = VARIABLE_SCOPES[scope]
    respx.get(f"{path}/v1").mock(return_value=Response(200, json={"uuid": "{v1}", "key": "A", "value": "plain"}))
    # Act
    variable = accessor(client).get("v1")
    # Assert
    assert variable.key == "A"
    assert variable.value is not None
    assert variable.value.get_secret_value() == "plain"


@VARIABLE_SCOPE
@respx.mock
def test_variables_update_puts_only_the_given_fields(client: BitbucketClient, scope: str) -> None:
    # Arrange
    accessor, path = VARIABLE_SCOPES[scope]
    route = respx.put(f"{path}/v1").mock(return_value=Response(200, json={"uuid": "{v1}", "key": "A"}))
    # Act
    variable = accessor(client).update("v1", PipelineVariableUpdate(value="next"))
    # Assert
    assert json.loads(route.calls[0].request.content) == {"value": "next"}
    assert variable.key == "A"


@VARIABLE_SCOPE
@respx.mock
def test_variables_delete_returns_none(client: BitbucketClient, scope: str) -> None:
    # Arrange
    accessor, path = VARIABLE_SCOPES[scope]
    route = respx.delete(f"{path}/v1").mock(return_value=Response(204))
    # Act
    result = accessor(client).delete("v1")
    # Assert
    assert route.called
    assert result is None


@VARIABLE_SCOPE
@respx.mock
def test_variables_get_raises_not_found(client: BitbucketClient, scope: str) -> None:
    # Arrange
    accessor, path = VARIABLE_SCOPES[scope]
    respx.get(f"{path}/missing").mock(return_value=Response(404, json={"type": "error"}))
    # Act
    with pytest.raises(NotFoundError) as raised:
        accessor(client).get("missing")
    # Assert
    assert raised.value.status_code == 404


@respx.mock
def test_variables_create_raises_conflict_without_leaking_the_value(client: BitbucketClient) -> None:
    # Arrange
    accessor, path = VARIABLE_SCOPES["repository"]
    respx.post(path).mock(return_value=Response(409, json={"type": "error", "error": {"message": "key exists"}}))
    payload = PipelineVariableCreate(key="TOKEN", value="s3cr3t-value", secured=True)
    # Act
    with pytest.raises(ConflictError) as raised:
        accessor(client).create(payload)
    # Assert
    assert "s3cr3t-value" not in str(raised.value)
    assert "s3cr3t-value" not in repr(raised.value)


@respx.mock
def test_variables_create_debug_log_never_contains_the_value(
    client: BitbucketClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Arrange
    accessor, path = VARIABLE_SCOPES["workspace"]
    respx.post(path).mock(return_value=Response(201, json={"key": "TOKEN"}))
    caplog.set_level(logging.DEBUG, logger="bitbucket")
    # Act
    accessor(client).create(PipelineVariableCreate(key="TOKEN", value="s3cr3t-value", secured=True))
    # Assert
    assert caplog.records
    assert "s3cr3t-value" not in caplog.text


def test_pipeline_variable_read_model_hides_the_value_in_repr() -> None:
    # Arrange
    # Act
    variable = PipelineVariable.model_validate({"key": "A", "value": "visible-only-by-call", "secured": False})
    # Assert
    assert "visible-only-by-call" not in repr(variable)
    assert variable.model_dump(mode="json")["value"] != "visible-only-by-call"


@RUNNER_SCOPE
@respx.mock
def test_runners_create_posts_name_and_labels(client: BitbucketClient, scope: str) -> None:
    # Arrange
    accessor, path = RUNNER_SCOPES[scope]
    route = respx.post(path).mock(
        return_value=Response(
            200,
            json={
                "uuid": "{r1}",
                "name": "linux",
                "labels": ["self.hosted", "linux"],
                "state": {"status": "UNREGISTERED", "version": {"version": "1.0"}},
                "oauth_client": {"id": "cid", "secret": "client-secret", "token_endpoint": "https://auth.example.com"},
            },
        ),
    )
    # Act
    runner = accessor(client).create(RunnerCreate(name="linux", labels=["self.hosted", "linux"]))
    # Assert
    assert json.loads(route.calls[0].request.content) == {"name": "linux", "labels": ["self.hosted", "linux"]}
    assert runner.state is not None
    assert runner.state.status is RunnerStatus.UNREGISTERED
    assert runner.oauth_client is not None
    assert runner.oauth_client.secret is not None
    assert runner.oauth_client.secret.get_secret_value() == "client-secret"
    assert "client-secret" not in repr(runner)


@RUNNER_SCOPE
@respx.mock
def test_runners_list_follows_next_cursor(client: BitbucketClient, scope: str) -> None:
    # Arrange
    accessor, path = RUNNER_SCOPES[scope]
    next_url = f"{BASE_URL}/runners-page-2/{scope}"
    respx.get(path).mock(return_value=Response(200, json={"values": [{"name": "a"}], "next": next_url}))
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{"name": "b"}]}))
    # Act
    runners = list(accessor(client).list())
    # Assert
    assert [runner.name for runner in runners] == ["a", "b"]


@RUNNER_SCOPE
@respx.mock
def test_runners_get_falls_back_to_unknown_for_a_new_status(client: BitbucketClient, scope: str) -> None:
    # Arrange
    accessor, path = RUNNER_SCOPES[scope]
    respx.get(f"{path}/r1").mock(return_value=Response(200, json={"state": {"status": "HIBERNATING"}}))
    # Act
    runner = accessor(client).get("r1")
    # Assert
    assert runner.state is not None
    assert runner.state.status is RunnerStatus.UNKNOWN


@RUNNER_SCOPE
@respx.mock
def test_runners_update_puts_the_new_labels(client: BitbucketClient, scope: str) -> None:
    # Arrange
    accessor, path = RUNNER_SCOPES[scope]
    route = respx.put(f"{path}/r1").mock(return_value=Response(200, json={"labels": ["gpu"]}))
    # Act
    runner = accessor(client).update("r1", RunnerUpdate(labels=["gpu"]))
    # Assert
    assert json.loads(route.calls[0].request.content) == {"labels": ["gpu"]}
    assert runner.labels == ["gpu"]


@RUNNER_SCOPE
@respx.mock
def test_runners_delete_returns_none(client: BitbucketClient, scope: str) -> None:
    # Arrange
    accessor, path = RUNNER_SCOPES[scope]
    route = respx.delete(f"{path}/r1").mock(return_value=Response(204))
    # Act
    result = accessor(client).delete("r1")
    # Assert
    assert route.called
    assert result is None
