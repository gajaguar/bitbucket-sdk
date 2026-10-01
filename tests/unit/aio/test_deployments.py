from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import respx
from httpx import Response

from bitbucket.models import DeployKeyCreate
from bitbucket.models import DeployKeyUpdate
from bitbucket.models import DeploymentStateName
from bitbucket.models import DeploymentStatusName
from bitbucket.models import EnvironmentCreate
from bitbucket.models import EnvironmentUpdate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.aio.client import AsyncBitbucketClient

REPO: Final = f"{BASE_URL}/repositories/ws/repo"
PROJECT: Final = f"{BASE_URL}/workspaces/ws/projects/KEY"
ENVIRONMENT_BODY: Final = {"type": "deployment_environment", "uuid": "{env-1}", "name": "Test"}
KEY_BODY: Final = {"type": "deploy_key", "id": 7, "key": "ssh-ed25519 AAAA", "label": "ci", "last_used": None}


def _repo(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").repository("repo")


@respx.mock
async def test_environments_list_follows_the_next_link(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    next_url = f"{REPO}/environments-page-2"
    respx.get(f"{REPO}/environments").mock(
        return_value=Response(200, json={"values": [ENVIRONMENT_BODY], "next": next_url})
    )
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{**ENVIRONMENT_BODY, "uuid": "{env-2}"}]}))
    # Act
    result = [item async for item in _repo(aclient).environments.list()]
    # Assert
    assert [environment.uuid for environment in result] == ["{env-1}", "{env-2}"]


@respx.mock
async def test_environments_get_reads_one_environment(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{REPO}/environments/{{env-1}}").mock(return_value=Response(200, json=ENVIRONMENT_BODY))
    # Act
    environment = await _repo(aclient).environments.get("{env-1}")
    # Assert
    assert environment.name == "Test"


@respx.mock
async def test_environments_create_always_sends_the_type(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{REPO}/environments").mock(return_value=Response(201, json=ENVIRONMENT_BODY))
    # Act
    environment = await _repo(aclient).environments.create(EnvironmentCreate(name="Test"))
    # Assert
    assert json.loads(route.calls[0].request.content) == {"type": "deployment_environment", "name": "Test"}
    assert environment.uuid == "{env-1}"


@respx.mock
async def test_environments_update_posts_to_changes_and_returns_nothing(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{REPO}/environments/{{env-1}}/changes").mock(return_value=Response(202))
    # Act
    result = await _repo(aclient).environments.update("{env-1}", EnvironmentUpdate(name="Staging"))
    # Assert
    assert result is None
    assert json.loads(route.calls[0].request.content) == {"name": "Staging"}


@respx.mock
async def test_environments_delete_sends_delete(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{REPO}/environments/{{env-1}}").mock(return_value=Response(204))
    # Act
    await _repo(aclient).environments.delete("{env-1}")
    # Assert
    assert route.called


@respx.mock
async def test_environment_variables_still_resolve_after_the_extension(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{REPO}/deployments_config/environments/{{env-1}}/variables").mock(
        return_value=Response(200, json={"values": []})
    )
    # Act
    result = [item async for item in _repo(aclient).environments.variables("{env-1}").list()]
    # Assert
    assert route.called
    assert not result


@respx.mock
async def test_deployments_list_follows_the_next_link(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    next_url = f"{REPO}/deployments-page-2"
    respx.get(f"{REPO}/deployments").mock(
        return_value=Response(200, json={"values": [{"uuid": "{d-1}"}], "next": next_url})
    )
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{"uuid": "{d-2}"}]}))
    # Act
    result = [item async for item in _repo(aclient).deployments.list()]
    # Assert
    assert [deployment.uuid for deployment in result] == ["{d-1}", "{d-2}"]


@respx.mock
async def test_deployments_get_parses_a_completed_state(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    body = {
        "uuid": "{d-1}",
        "state": {
            "type": "deployment_state_completed",
            "name": "COMPLETED",
            "status": {"type": "deployment_state_completed_status_failed", "name": "FAILED"},
            "start_date": "2026-01-02T03:04:05.000000+00:00",
        },
        "environment": ENVIRONMENT_BODY,
        "release": {"uuid": "{r-1}", "name": "v1", "commit": {"hash": "abc"}},
    }
    respx.get(f"{REPO}/deployments/{{d-1}}").mock(return_value=Response(200, json=body))
    # Act
    deployment = await _repo(aclient).deployments.get("{d-1}")
    # Assert
    assert deployment.state is not None
    assert deployment.state.name is DeploymentStateName.COMPLETED
    assert deployment.state.status is not None
    assert deployment.state.status.name is DeploymentStatusName.FAILED
    assert deployment.environment is not None
    assert deployment.environment.name == "Test"
    assert deployment.release is not None
    assert deployment.release.name == "v1"


@respx.mock
async def test_deployments_get_maps_an_unlisted_state_to_unknown(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{REPO}/deployments/{{d-1}}").mock(return_value=Response(200, json={"state": {"name": "ROLLING_BACK"}}))
    # Act
    deployment = await _repo(aclient).deployments.get("{d-1}")
    # Assert
    assert deployment.state is not None
    assert deployment.state.name is DeploymentStateName.UNKNOWN


@respx.mock
async def test_repository_deploy_keys_list_follows_the_next_link(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    next_url = f"{REPO}/deploy-keys-page-2"
    respx.get(f"{REPO}/deploy-keys").mock(return_value=Response(200, json={"values": [KEY_BODY], "next": next_url}))
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{**KEY_BODY, "id": 8}]}))
    # Act
    result = [item async for item in _repo(aclient).deploy_keys.list()]
    # Assert
    assert [key.id for key in result] == [7, 8]
    assert result[0].last_used is None


@respx.mock
async def test_repository_deploy_keys_get_create_update_and_delete(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{REPO}/deploy-keys/7").mock(return_value=Response(200, json=KEY_BODY))
    created = respx.post(f"{REPO}/deploy-keys").mock(return_value=Response(200, json=KEY_BODY))
    updated = respx.put(f"{REPO}/deploy-keys/7").mock(return_value=Response(200, json={**KEY_BODY, "label": "new"}))
    deleted = respx.delete(f"{REPO}/deploy-keys/7").mock(return_value=Response(204))
    keys = _repo(aclient).deploy_keys
    # Act
    fetched = await keys.get(7)
    await keys.create(DeployKeyCreate(key="ssh-ed25519 AAAA", label="ci"))
    renamed = await keys.update(7, DeployKeyUpdate(key="ssh-ed25519 AAAA", label="new"))
    await keys.delete(7)
    # Assert
    assert fetched.key == "ssh-ed25519 AAAA"
    assert json.loads(created.calls[0].request.content) == {"key": "ssh-ed25519 AAAA", "label": "ci"}
    assert json.loads(updated.calls[0].request.content) == {"key": "ssh-ed25519 AAAA", "label": "new"}
    assert renamed.label == "new"
    assert deleted.called


@respx.mock
async def test_project_deploy_keys_list_get_create_and_delete(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    body = {**KEY_BODY, "project": {"key": "KEY"}, "created_by": {"type": "user"}}
    next_url = f"{PROJECT}/deploy-keys-page-2"
    respx.get(f"{PROJECT}/deploy-keys").mock(return_value=Response(200, json={"values": [body], "next": next_url}))
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{**body, "id": 8}]}))
    respx.get(f"{PROJECT}/deploy-keys/7").mock(return_value=Response(200, json=body))
    created = respx.post(f"{PROJECT}/deploy-keys").mock(return_value=Response(200, json=body))
    deleted = respx.delete(f"{PROJECT}/deploy-keys/7").mock(return_value=Response(204))
    keys = aclient.workspace("ws").project("KEY").deploy_keys
    # Act
    listed = [item async for item in keys.list()]
    fetched = await keys.get(7)
    await keys.create(DeployKeyCreate(key="ssh-ed25519 AAAA"))
    await keys.delete(7)
    # Assert
    assert [key.id for key in listed] == [7, 8]
    assert fetched.project is not None
    assert fetched.project.key == "KEY"
    assert json.loads(created.calls[0].request.content) == {"key": "ssh-ed25519 AAAA"}
    assert deleted.called
