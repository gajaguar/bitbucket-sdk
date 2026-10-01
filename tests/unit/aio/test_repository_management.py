from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

from bitbucket.models.hook import WebhookCreate
from bitbucket.models.hook import WebhookUpdate
from bitbucket.models.permission import GroupPermissionUpdate
from bitbucket.models.permission import RepositoryOverrideSettings
from bitbucket.models.permission import UserPermissionUpdate
from bitbucket.models.repository import ForkCreate
from bitbucket.models.repository import RepositoryCreate
from bitbucket.models.repository import RepositoryUpdate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.aio.client import AsyncBitbucketClient


def _repositories(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").repositories


def _repository(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").repository("repo")


@respx.mock
async def test_repository_create_posts_to_the_slug_path(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo").mock(
        return_value=Response(200, json={"name": "repo", "scm": "git"}),
    )
    payload = RepositoryCreate(description="new repo", is_private=True)
    # Act
    result = await _repositories(aclient).create("repo", payload)
    # Assert
    assert result.name == "repo"
    assert route.calls[0].request.content == b'{"description":"new repo","is_private":true}'


@respx.mock
async def test_repository_update_puts_only_the_changed_description(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo").mock(
        return_value=Response(200, json={"name": "repo", "description": "updated"}),
    )
    # Act
    result = await _repositories(aclient).update("repo", RepositoryUpdate(description="updated"))
    # Assert
    assert result.description == "updated"
    assert route.calls[0].request.content == b'{"description":"updated"}'


@respx.mock
async def test_repository_delete_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo").mock(return_value=Response(204))
    # Act
    result = await _repositories(aclient).delete("repo")
    # Assert
    assert result is None
    assert route.called


@respx.mock
async def test_repository_create_fork_posts_target_name(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/forks").mock(
        return_value=Response(200, json={"name": "repo-fork"}),
    )
    # Act
    result = await _repositories(aclient).create_fork("repo", ForkCreate(name="repo-fork"))
    # Assert
    assert result.name == "repo-fork"
    assert route.calls[0].request.content == b'{"name":"repo-fork"}'


@respx.mock
async def test_repository_forks_returns_fork_list(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/forks").mock(
        return_value=Response(200, json={"values": [{"name": "fork-1"}], "next": None}),
    )
    # Act
    forks = [item async for item in _repositories(aclient).forks("repo")]
    # Assert
    assert [fork.name for fork in forks] == ["fork-1"]


@respx.mock
async def test_repository_watchers_returns_watcher_accounts(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/watchers").mock(
        return_value=Response(200, json={"values": [{"uuid": "{x}"}], "next": None}),
    )
    # Act
    watchers = [item async for item in _repositories(aclient).watchers("repo")]
    # Assert
    assert [watcher.uuid for watcher in watchers] == ["{x}"]


@respx.mock
async def test_repository_hook_create_posts_url_and_events(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/hooks").mock(
        return_value=Response(200, json={"uuid": "{h}"}),
    )
    payload = WebhookCreate(description="ci", url="https://ci.example.com/hook", events=["repo:push"])
    # Act
    result = await _repository(aclient).hooks.create(payload)
    # Assert
    assert result.uuid == "{h}"
    assert route.calls[0].request.content == (
        b'{"description":"ci","url":"https://ci.example.com/hook","events":["repo:push"]}'
    )


@respx.mock
async def test_repository_hook_list_returns_configured_hooks(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/hooks").mock(
        return_value=Response(200, json={"values": [{"uuid": "{h}"}], "next": None}),
    )
    # Act
    hooks = [item async for item in _repository(aclient).hooks.list()]
    # Assert
    assert [hook.uuid for hook in hooks] == ["{h}"]


@respx.mock
async def test_repository_hook_update_puts_new_url(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/hooks/{{h}}").mock(
        return_value=Response(200, json={"uuid": "{h}", "url": "https://new.example.com"}),
    )
    # Act
    result = await _repository(aclient).hooks.update("{h}", WebhookUpdate(url="https://new.example.com"))
    # Assert
    assert result.url == "https://new.example.com"
    assert route.calls[0].request.content == b'{"url":"https://new.example.com"}'


@respx.mock
async def test_repository_hook_delete_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/hooks/{{h}}").mock(return_value=Response(204))
    # Act
    result = await _repository(aclient).hooks.delete("{h}")
    # Assert
    assert result is None
    assert route.called


@respx.mock
async def test_repository_group_permission_list_returns_group_permissions(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/permissions-config/groups").mock(
        return_value=Response(200, json={"values": [{"permission": "write"}], "next": None}),
    )
    # Act
    permissions = [item async for item in _repository(aclient).permissions.groups.list()]
    # Assert
    assert [permission.permission for permission in permissions] == ["write"]


@respx.mock
async def test_repository_group_permission_update_puts_permission_level(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/permissions-config/groups/engineers").mock(
        return_value=Response(200, json={"permission": "admin"}),
    )
    # Act
    result = await _repository(aclient).permissions.groups.update(
        "engineers", GroupPermissionUpdate(permission="admin")
    )
    # Assert
    assert result.permission == "admin"
    assert route.calls[0].request.content == b'{"permission":"admin"}'


@respx.mock
async def test_repository_group_permission_delete_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/permissions-config/groups/engineers").mock(
        return_value=Response(204),
    )
    # Act
    result = await _repository(aclient).permissions.groups.delete("engineers")
    # Assert
    assert result is None
    assert route.called


@respx.mock
async def test_repository_user_permission_get_returns_permission(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/permissions-config/users/{{u}}").mock(
        return_value=Response(200, json={"permission": "read"}),
    )
    # Act
    result = await _repository(aclient).permissions.users.get("{u}")
    # Assert
    assert result.permission == "read"


@respx.mock
async def test_repository_user_permission_update_puts_permission_level(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/permissions-config/users/{{u}}").mock(
        return_value=Response(200, json={"permission": "write"}),
    )
    # Act
    result = await _repository(aclient).permissions.users.update("{u}", UserPermissionUpdate(permission="write"))
    # Assert
    assert result.permission == "write"
    assert route.calls[0].request.content == b'{"permission":"write"}'


@respx.mock
async def test_repository_override_settings_returns_current_settings(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/override-settings").mock(
        return_value=Response(
            200, json={"type": "repository_inheritance_state", "override_settings": {"branching_model": True}}
        ),
    )
    # Act
    result = await _repository(aclient).permissions.override_settings()
    # Assert
    assert result.override_settings is not None
    assert result.override_settings.branching_model is True


@respx.mock
async def test_repository_override_settings_update_puts_new_settings(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/override-settings").mock(
        return_value=Response(204),
    )
    # Act
    await _repository(aclient).permissions.update_override_settings(RepositoryOverrideSettings(branching_model=False))
    # Assert
    assert route.calls[0].request.content == b'{"override_settings":{"branching_model":false}}'
