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
    from bitbucket.client import BitbucketClient


def _repositories(client: BitbucketClient):
    return client.workspace("ws").repositories


def _repository(client: BitbucketClient):
    return client.workspace("ws").repository("repo")


@respx.mock
def test_repository_create_posts_to_the_slug_path(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo").mock(
        return_value=Response(200, json={"name": "repo", "scm": "git"}),
    )
    payload = RepositoryCreate(description="new repo", is_private=True)
    # Act
    result = _repositories(client).create("repo", payload)
    # Assert
    assert result.name == "repo"
    assert route.calls[0].request.content == b'{"description":"new repo","is_private":true}'


@respx.mock
def test_repository_update_puts_only_the_changed_description(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo").mock(
        return_value=Response(200, json={"name": "repo", "description": "updated"}),
    )
    # Act
    result = _repositories(client).update("repo", RepositoryUpdate(description="updated"))
    # Assert
    assert result.description == "updated"
    assert route.calls[0].request.content == b'{"description":"updated"}'


@respx.mock
def test_repository_delete_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo").mock(return_value=Response(204))
    # Act
    result = _repositories(client).delete("repo")
    # Assert
    assert result is None
    assert route.called


@respx.mock
def test_repository_create_fork_posts_target_name(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/forks").mock(
        return_value=Response(200, json={"name": "repo-fork"}),
    )
    # Act
    result = _repositories(client).create_fork("repo", ForkCreate(name="repo-fork"))
    # Assert
    assert result.name == "repo-fork"
    assert route.calls[0].request.content == b'{"name":"repo-fork"}'


@respx.mock
def test_repository_forks_returns_fork_list(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/forks").mock(
        return_value=Response(200, json={"values": [{"name": "fork-1"}], "next": None}),
    )
    # Act
    forks = list(_repositories(client).forks("repo"))
    # Assert
    assert [fork.name for fork in forks] == ["fork-1"]


@respx.mock
def test_repository_watchers_returns_watcher_accounts(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/watchers").mock(
        return_value=Response(200, json={"values": [{"uuid": "{x}"}], "next": None}),
    )
    # Act
    watchers = list(_repositories(client).watchers("repo"))
    # Assert
    assert [watcher.uuid for watcher in watchers] == ["{x}"]


@respx.mock
def test_repository_hook_create_posts_url_and_events(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/hooks").mock(
        return_value=Response(200, json={"uuid": "{h}"}),
    )
    payload = WebhookCreate(description="ci", url="https://ci.example.com/hook", events=["repo:push"])
    # Act
    result = _repository(client).hooks.create(payload)
    # Assert
    assert result.uuid == "{h}"
    assert route.calls[0].request.content == (
        b'{"description":"ci","url":"https://ci.example.com/hook","events":["repo:push"]}'
    )


@respx.mock
def test_repository_hook_list_returns_configured_hooks(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/hooks").mock(
        return_value=Response(200, json={"values": [{"uuid": "{h}"}], "next": None}),
    )
    # Act
    hooks = list(_repository(client).hooks.list())
    # Assert
    assert [hook.uuid for hook in hooks] == ["{h}"]


@respx.mock
def test_repository_hook_update_puts_new_url(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/hooks/{{h}}").mock(
        return_value=Response(200, json={"uuid": "{h}", "url": "https://new.example.com"}),
    )
    # Act
    result = _repository(client).hooks.update("{h}", WebhookUpdate(url="https://new.example.com"))
    # Assert
    assert result.url == "https://new.example.com"
    assert route.calls[0].request.content == b'{"url":"https://new.example.com"}'


@respx.mock
def test_repository_hook_delete_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/hooks/{{h}}").mock(return_value=Response(204))
    # Act
    result = _repository(client).hooks.delete("{h}")
    # Assert
    assert result is None
    assert route.called


@respx.mock
def test_repository_group_permission_list_returns_group_permissions(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/permissions-config/groups").mock(
        return_value=Response(200, json={"values": [{"permission": "write"}], "next": None}),
    )
    # Act
    permissions = list(_repository(client).permissions.groups.list())
    # Assert
    assert [permission.permission for permission in permissions] == ["write"]


@respx.mock
def test_repository_group_permission_update_puts_permission_level(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/permissions-config/groups/engineers").mock(
        return_value=Response(200, json={"permission": "admin"}),
    )
    # Act
    result = _repository(client).permissions.groups.update("engineers", GroupPermissionUpdate(permission="admin"))
    # Assert
    assert result.permission == "admin"
    assert route.calls[0].request.content == b'{"permission":"admin"}'


@respx.mock
def test_repository_group_permission_delete_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/permissions-config/groups/engineers").mock(
        return_value=Response(204),
    )
    # Act
    result = _repository(client).permissions.groups.delete("engineers")
    # Assert
    assert result is None
    assert route.called


@respx.mock
def test_repository_user_permission_get_returns_permission(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/permissions-config/users/{{u}}").mock(
        return_value=Response(200, json={"permission": "read"}),
    )
    # Act
    result = _repository(client).permissions.users.get("{u}")
    # Assert
    assert result.permission == "read"


@respx.mock
def test_repository_user_permission_update_puts_permission_level(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/permissions-config/users/{{u}}").mock(
        return_value=Response(200, json={"permission": "write"}),
    )
    # Act
    result = _repository(client).permissions.users.update("{u}", UserPermissionUpdate(permission="write"))
    # Assert
    assert result.permission == "write"
    assert route.calls[0].request.content == b'{"permission":"write"}'


@respx.mock
def test_repository_override_settings_returns_current_settings(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/permissions-config/override-settings").mock(
        return_value=Response(200, json={"branching_model": True}),
    )
    # Act
    result = _repository(client).permissions.override_settings()
    # Assert
    assert result.branching_model is True


@respx.mock
def test_repository_override_settings_update_puts_new_settings(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/permissions-config/override-settings").mock(
        return_value=Response(200, json={"branching_model": False}),
    )
    # Act
    result = _repository(client).permissions.update_override_settings(
        RepositoryOverrideSettings(branching_model=False)
    )
    # Assert
    assert result.branching_model is False
    assert route.calls[0].request.content == b'{"branching_model":false}'
