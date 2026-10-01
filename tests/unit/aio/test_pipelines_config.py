from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import pytest
import respx
from httpx import Response

from bitbucket.errors import NotFoundError
from bitbucket.models import PipelineBuildNumberUpdate
from bitbucket.models import PipelineKnownHostCreate
from bitbucket.models import PipelineKnownHostUpdate
from bitbucket.models import PipelineRefType
from bitbucket.models import PipelineScheduleCreate
from bitbucket.models import PipelineScheduleTargetCreate
from bitbucket.models import PipelineScheduleUpdate
from bitbucket.models import PipelineSelector
from bitbucket.models import PipelineSelectorType
from bitbucket.models import PipelineSshKeyPairUpdate
from bitbucket.models import PipelineSshPublicKey
from bitbucket.models import PipelineVariableCreate
from bitbucket.models import PipelineVariableUpdate
from bitbucket.models import PipelinesConfigUpdate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.aio.client import AsyncBitbucketClient

REPO: Final = f"{BASE_URL}/repositories/ws/repo"
CONFIG: Final = f"{REPO}/pipelines_config"
HYPHEN_CONFIG: Final = f"{REPO}/pipelines-config"


def _config(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").repository("repo").pipelines_config


@respx.mock
async def test_pipelines_config_get_returns_the_enabled_flag(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(CONFIG).mock(
        return_value=Response(200, json={"type": "repository_pipelines_configuration", "enabled": True})
    )
    # Act
    config = await _config(aclient).get()
    # Assert
    assert config.enabled is True


@respx.mock
async def test_pipelines_config_update_puts_the_enabled_flag(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(CONFIG).mock(return_value=Response(200, json={"enabled": False}))
    # Act
    config = await _config(aclient).update(PipelinesConfigUpdate(enabled=False))
    # Assert
    assert json.loads(route.calls[0].request.content) == {"enabled": False}
    assert config.enabled is False


@respx.mock
async def test_pipelines_config_update_build_number_puts_the_next_number(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{CONFIG}/build_number").mock(return_value=Response(200, json={"next": 500}))
    # Act
    build_number = await _config(aclient).update_build_number(PipelineBuildNumberUpdate(next=500))
    # Assert
    assert json.loads(route.calls[0].request.content) == {"next": 500}
    assert build_number.next == 500


@respx.mock
async def test_schedules_create_posts_the_target_with_its_type(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{CONFIG}/schedules").mock(return_value=Response(201, json={"uuid": "{s1}", "enabled": True}))
    payload = PipelineScheduleCreate(
        target=PipelineScheduleTargetCreate(
            ref_type=PipelineRefType.BRANCH,
            ref_name="main",
            selector=PipelineSelector(type=PipelineSelectorType.BRANCHES, pattern="main"),
        ),
        cron_pattern="0 0 12 * * ? *",
        enabled=True,
    )
    # Act
    schedule = await _config(aclient).schedules.create(payload)
    # Assert
    assert json.loads(route.calls[0].request.content) == {
        "target": {
            "type": "pipeline_ref_target",
            "ref_type": "branch",
            "ref_name": "main",
            "selector": {"type": "branches", "pattern": "main"},
        },
        "cron_pattern": "0 0 12 * * ? *",
        "enabled": True,
    }
    assert schedule.uuid == "{s1}"


@respx.mock
async def test_schedules_list_follows_next_cursor(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    next_url = f"{REPO}/schedules-page-2"
    respx.get(f"{CONFIG}/schedules").mock(
        return_value=Response(200, json={"values": [{"uuid": "{a}"}], "next": next_url}),
    )
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{"uuid": "{b}"}]}))
    # Act
    schedules = [item async for item in _config(aclient).schedules.list()]
    # Assert
    assert [schedule.uuid for schedule in schedules] == ["{a}", "{b}"]


@respx.mock
async def test_schedules_get_parses_the_target(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{CONFIG}/schedules/s1").mock(
        return_value=Response(
            200,
            json={
                "uuid": "{s1}",
                "cron_pattern": "0 0 * * * ? *",
                "target": {"ref_type": "branch", "ref_name": "main", "selector": {"type": "custom", "pattern": "x"}},
            },
        ),
    )
    # Act
    schedule = await _config(aclient).schedules.get("s1")
    # Assert
    assert schedule.target is not None
    assert schedule.target.ref_type is PipelineRefType.BRANCH
    assert schedule.target.selector is not None
    assert schedule.target.selector.type is PipelineSelectorType.CUSTOM


@respx.mock
async def test_schedules_update_puts_the_enabled_flag(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{CONFIG}/schedules/s1").mock(return_value=Response(200, json={"enabled": False}))
    # Act
    schedule = await _config(aclient).schedules.update("s1", PipelineScheduleUpdate(enabled=False))
    # Assert
    assert json.loads(route.calls[0].request.content) == {"enabled": False}
    assert schedule.enabled is False


@respx.mock
async def test_schedules_delete_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{CONFIG}/schedules/s1").mock(return_value=Response(204))
    # Act
    result = await _config(aclient).schedules.delete("s1")
    # Assert
    assert route.called
    assert result is None


@respx.mock
async def test_schedules_executions_follow_next_and_tell_executed_from_errored(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    next_url = f"{REPO}/executions-page-2"
    respx.get(f"{CONFIG}/schedules/s1/executions").mock(
        return_value=Response(
            200,
            json={
                "values": [{"type": "pipeline_schedule_execution_executed", "pipeline": {"uuid": "{p}"}}],
                "next": next_url,
            },
        ),
    )
    respx.get(next_url).mock(
        return_value=Response(
            200,
            json={"values": [{"type": "pipeline_schedule_execution_errored", "error": {"key": "k", "message": "m"}}]},
        ),
    )
    # Act
    executions = [item async for item in _config(aclient).schedules.executions("s1")]
    # Assert
    assert executions[0].pipeline is not None
    assert executions[0].pipeline.uuid == "{p}"
    assert executions[1].error is not None
    assert executions[1].error.message == "m"


@respx.mock
async def test_ssh_key_pair_get_returns_the_public_key_only(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{CONFIG}/ssh/key_pair").mock(return_value=Response(200, json={"public_key": "ssh-rsa AAA"}))
    # Act
    key_pair = await _config(aclient).ssh_key_pair.get()
    # Assert
    assert key_pair.public_key == "ssh-rsa AAA"
    assert key_pair.private_key is None


@respx.mock
async def test_ssh_key_pair_update_sends_the_key_and_masks_its_text_form(
    aclient: AsyncBitbucketClient,
) -> None:
    # Arrange
    route = respx.put(f"{CONFIG}/ssh/key_pair").mock(return_value=Response(200, json={"public_key": "ssh-rsa AAA"}))
    payload = PipelineSshKeyPairUpdate(private_key="-----BEGIN PRIVATE KEY-----\nsecret", public_key="ssh-rsa AAA")
    # Act
    key_pair = await _config(aclient).ssh_key_pair.update(payload)
    # Assert
    assert json.loads(route.calls[0].request.content) == {
        "private_key": "-----BEGIN PRIVATE KEY-----\nsecret",
        "public_key": "ssh-rsa AAA",
    }
    assert "secret" not in repr(payload)
    assert "secret" not in repr(key_pair)


@respx.mock
async def test_ssh_key_pair_read_model_masks_the_key_in_its_text_form(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{CONFIG}/ssh/key_pair").mock(
        return_value=Response(200, json={"private_key": "topsecret", "public_key": "ssh-rsa AAA"}),
    )
    # Act
    key_pair = await _config(aclient).ssh_key_pair.get()
    # Assert
    assert "topsecret" not in repr(key_pair)
    assert "topsecret" not in str(key_pair)


@respx.mock
async def test_ssh_key_pair_delete_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{CONFIG}/ssh/key_pair").mock(return_value=Response(204))
    # Act
    result = await _config(aclient).ssh_key_pair.delete()
    # Assert
    assert route.called
    assert result is None


@respx.mock
async def test_ssh_key_pair_get_raises_not_found_when_none_is_set(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{CONFIG}/ssh/key_pair").mock(return_value=Response(404, json={"type": "error"}))
    # Act
    with pytest.raises(NotFoundError) as raised:
        await _config(aclient).ssh_key_pair.get()
    # Assert
    assert raised.value.status_code == 404


@respx.mock
async def test_known_hosts_create_posts_hostname_and_public_key(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{CONFIG}/ssh/known_hosts").mock(
        return_value=Response(201, json={"uuid": "{k1}", "hostname": "example.com"}),
    )
    payload = PipelineKnownHostCreate(
        hostname="example.com",
        public_key=PipelineSshPublicKey(key_type="ssh-ed25519", key="AAAA"),
    )
    # Act
    host = await _config(aclient).known_hosts.create(payload)
    # Assert
    assert json.loads(route.calls[0].request.content) == {
        "hostname": "example.com",
        "public_key": {"key_type": "ssh-ed25519", "key": "AAAA"},
    }
    assert host.uuid == "{k1}"


@respx.mock
async def test_known_hosts_list_follows_next_cursor(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    next_url = f"{REPO}/known-hosts-page-2"
    respx.get(f"{CONFIG}/ssh/known_hosts").mock(
        return_value=Response(200, json={"values": [{"hostname": "a"}], "next": next_url}),
    )
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{"hostname": "b"}]}))
    # Act
    hosts = [item async for item in _config(aclient).known_hosts.list()]
    # Assert
    assert [host.hostname for host in hosts] == ["a", "b"]


@respx.mock
async def test_known_hosts_get_parses_fingerprints(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{CONFIG}/ssh/known_hosts/k1").mock(
        return_value=Response(
            200,
            json={"hostname": "example.com", "public_key": {"key_type": "ssh-rsa", "sha256_fingerprint": "SHA256:x"}},
        ),
    )
    # Act
    host = await _config(aclient).known_hosts.get("k1")
    # Assert
    assert host.public_key is not None
    assert host.public_key.sha256_fingerprint == "SHA256:x"


@respx.mock
async def test_known_hosts_update_puts_the_new_hostname(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{CONFIG}/ssh/known_hosts/k1").mock(
        return_value=Response(200, json={"hostname": "new.example.com"})
    )
    # Act
    host = await _config(aclient).known_hosts.update("k1", PipelineKnownHostUpdate(hostname="new.example.com"))
    # Assert
    assert json.loads(route.calls[0].request.content) == {"hostname": "new.example.com"}
    assert host.hostname == "new.example.com"


@respx.mock
async def test_known_hosts_delete_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{CONFIG}/ssh/known_hosts/k1").mock(return_value=Response(204))
    # Act
    result = await _config(aclient).known_hosts.delete("k1")
    # Assert
    assert route.called
    assert result is None


@respx.mock
async def test_caches_list_uses_the_hyphenated_path_and_follows_next(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    next_url = f"{REPO}/caches-page-2"
    respx.get(f"{HYPHEN_CONFIG}/caches").mock(
        return_value=Response(200, json={"values": [{"name": "pip", "file_size_bytes": 10}], "next": next_url}),
    )
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{"name": "npm"}]}))
    # Act
    caches = [item async for item in _config(aclient).caches.list()]
    # Assert
    assert [cache.name for cache in caches] == ["pip", "npm"]
    assert caches[0].file_size_bytes == 10


@respx.mock
async def test_caches_delete_by_uuid_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{HYPHEN_CONFIG}/caches/c1").mock(return_value=Response(204))
    # Act
    result = await _config(aclient).caches.delete("c1")
    # Assert
    assert route.called
    assert result is None


@respx.mock
async def test_caches_delete_by_name_sends_the_name_query(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{HYPHEN_CONFIG}/caches").mock(return_value=Response(204))
    # Act
    result = await _config(aclient).caches.delete_by_name("pip")
    # Assert
    assert route.calls[0].request.url.params["name"] == "pip"
    assert result is None


@respx.mock
async def test_caches_content_uri_returns_the_uri(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{HYPHEN_CONFIG}/caches/c1/content-uri").mock(
        return_value=Response(200, json={"uri": "https://cache.example.com/c1"}),
    )
    # Act
    content = await _config(aclient).caches.content_uri("c1")
    # Assert
    assert content.uri == "https://cache.example.com/c1"


@respx.mock
async def test_workspace_oidc_configuration_returns_the_raw_json(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    document = {"issuer": "https://api.bitbucket.org/2.0/workspaces/ws/pipelines-config/identity/oidc"}
    route = respx.get(
        f"{BASE_URL}/workspaces/ws/pipelines-config/identity/oidc/.well-known/openid-configuration",
    ).mock(return_value=Response(200, json=document))
    # Act
    configuration = await aclient.workspace("ws").pipelines_config.oidc_configuration()
    # Assert
    assert route.called
    assert configuration == document


@respx.mock
async def test_workspace_oidc_keys_returns_the_raw_json(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    keys = {"keys": [{"kty": "RSA", "kid": "k1"}]}
    respx.get(f"{BASE_URL}/workspaces/ws/pipelines-config/identity/oidc/keys.json").mock(
        return_value=Response(200, json=keys),
    )
    # Act
    result = await aclient.workspace("ws").pipelines_config.oidc_keys()
    # Assert
    assert result == keys


@respx.mock
async def test_workspace_oidc_raises_not_found_for_an_unknown_workspace(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/workspaces/ws/pipelines-config/identity/oidc/keys.json").mock(
        return_value=Response(404, json={"type": "error"}),
    )
    # Act
    with pytest.raises(NotFoundError) as raised:
        await aclient.workspace("ws").pipelines_config.oidc_keys()
    # Assert
    assert raised.value.status_code == 404


ENVIRONMENT: Final = f"{REPO}/deployments_config/environments/env1/variables"


def _environment_variables(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").repository("repo").environments.variables("env1")


@respx.mock
async def test_environment_variables_list_follows_next_cursor(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    next_url = f"{REPO}/environment-variables-page-2"
    respx.get(ENVIRONMENT).mock(return_value=Response(200, json={"values": [{"key": "A"}], "next": next_url}))
    respx.get(next_url).mock(return_value=Response(200, json={"values": [{"key": "B"}]}))
    # Act
    variables = [item async for item in _environment_variables(aclient).list()]
    # Assert
    assert [variable.key for variable in variables] == ["A", "B"]


@respx.mock
async def test_environment_variables_create_posts_and_hides_the_value(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(ENVIRONMENT).mock(
        return_value=Response(201, json={"uuid": "{v1}", "key": "TOKEN", "secured": True})
    )
    payload = PipelineVariableCreate(key="TOKEN", value="s3cr3t", secured=True)
    # Act
    variable = await _environment_variables(aclient).create(payload)
    # Assert
    assert json.loads(route.calls[0].request.content) == {"key": "TOKEN", "value": "s3cr3t", "secured": True}
    assert variable.secured is True
    assert "s3cr3t" not in repr(payload)


@respx.mock
async def test_environment_variables_update_puts_the_new_value(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{ENVIRONMENT}/v1").mock(return_value=Response(200, json={"uuid": "{v1}", "key": "TOKEN"}))
    # Act
    variable = await _environment_variables(aclient).update("v1", PipelineVariableUpdate(value="new"))
    # Assert
    assert json.loads(route.calls[0].request.content) == {"value": "new"}
    assert variable.key == "TOKEN"


@respx.mock
async def test_environment_variables_delete_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{ENVIRONMENT}/v1").mock(return_value=Response(204))
    # Act
    result = await _environment_variables(aclient).delete("v1")
    # Assert
    assert route.called
    assert result is None
