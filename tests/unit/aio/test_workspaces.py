from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import respx
from httpx import Response

from bitbucket.models.permission import PermissionLevel
from bitbucket.models.workspace import WorkspaceForkingMode
from bitbucket.models.workspace import WorkspacePermissionLevel
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.aio.client import AsyncBitbucketClient

WORKSPACE: Final = f"{BASE_URL}/workspaces/ws"
WORKSPACE_BODY: Final = {"type": "workspace", "slug": "ws", "name": "WS", "forking_mode": "allow_forks"}
MEMBERSHIP: Final = {
    "type": "workspace_membership",
    "permission": "owner",
    "user": {"type": "user", "account_id": "acc-1", "display_name": "Ada"},
    "workspace": WORKSPACE_BODY,
}
REPO_PERMISSION: Final = {
    "type": "repository_permission",
    "permission": "admin",
    "user": {"type": "user", "account_id": "acc-1"},
    "repository": {"type": "repository", "slug": "repo"},
}


@respx.mock
async def test_workspace_get_returns_the_workspace(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(WORKSPACE).mock(return_value=Response(200, json=WORKSPACE_BODY))
    # Act
    result = await aclient.workspace("ws").get()
    # Assert
    assert route.called
    assert result.slug == "ws"
    assert result.forking_mode is WorkspaceForkingMode.ALLOW_FORKS


@respx.mock
async def test_workspace_unknown_forking_mode_maps_to_unknown(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(WORKSPACE).mock(return_value=Response(200, json={**WORKSPACE_BODY, "forking_mode": "something_new"}))
    # Act
    result = await aclient.workspace("ws").get()
    # Assert
    assert result.forking_mode is WorkspaceForkingMode.UNKNOWN


@respx.mock
async def test_workspace_gpg_public_key_returns_the_plain_text(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{WORKSPACE}/settings/gpg/public-key").mock(
        return_value=Response(200, text="-----BEGIN PGP PUBLIC KEY BLOCK-----")
    )
    # Act
    result = await aclient.workspace("ws").gpg_public_key()
    # Assert
    assert route.called
    assert result == "-----BEGIN PGP PUBLIC KEY BLOCK-----"


@respx.mock
async def test_members_list_and_get_use_the_members_path(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    list_route = respx.get(f"{WORKSPACE}/members").mock(return_value=Response(200, json={"values": [MEMBERSHIP]}))
    get_route = respx.get(f"{WORKSPACE}/members/acc-1").mock(return_value=Response(200, json=MEMBERSHIP))
    members = aclient.workspace("ws").members
    # Act
    listed = [item async for item in members.list()]
    got = await members.get("acc-1")
    # Assert
    assert list_route.called
    assert get_route.called
    assert listed[0].permission is WorkspacePermissionLevel.OWNER
    assert got.user is not None
    assert got.user.account_id == "acc-1"


@respx.mock
async def test_members_list_follows_the_next_link(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    next_url = f"{WORKSPACE}/members?page=2"
    respx.get(f"{WORKSPACE}/members", params={"page": "2"}).mock(
        return_value=Response(200, json={"values": [{**MEMBERSHIP, "permission": "member"}]})
    )
    respx.get(f"{WORKSPACE}/members").mock(return_value=Response(200, json={"values": [MEMBERSHIP], "next": next_url}))
    # Act
    result = [item async for item in aclient.workspace("ws").members.list()]
    # Assert
    assert [member.permission for member in result] == [
        WorkspacePermissionLevel.OWNER,
        WorkspacePermissionLevel.MEMBER,
    ]


@respx.mock
async def test_permissions_list_sends_the_filter(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{WORKSPACE}/permissions", params={"q": 'permission="owner"'}).mock(
        return_value=Response(200, json={"values": [MEMBERSHIP]})
    )
    # Act
    result = [item async for item in aclient.workspace("ws").permissions.list(q='permission="owner"')]
    # Assert
    assert route.called
    assert result[0].permission is WorkspacePermissionLevel.OWNER


@respx.mock
async def test_permissions_repositories_send_filter_and_sort(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(
        f"{WORKSPACE}/permissions/repositories", params={"q": 'permission>"read"', "sort": "user.display_name"}
    ).mock(return_value=Response(200, json={"values": [{**REPO_PERMISSION, "permission": "none"}]}))
    # Act
    result = [
        item
        async for item in aclient.workspace("ws").permissions.repositories(
            q='permission>"read"', sort="user.display_name"
        )
    ]
    # Assert
    assert route.called
    assert result[0].permission is PermissionLevel.NONE


@respx.mock
async def test_permissions_repository_uses_the_repo_slug_path(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{WORKSPACE}/permissions/repositories/repo").mock(
        return_value=Response(200, json={"values": [REPO_PERMISSION]})
    )
    # Act
    result = [item async for item in aclient.workspace("ws").permissions.repository("repo")]
    # Assert
    assert route.called
    assert result[0].repository is not None
    assert result[0].repository.slug == "repo"


@respx.mock
async def test_my_permission_uses_the_user_path(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/user/workspaces/ws/permission").mock(return_value=Response(200, json=MEMBERSHIP))
    # Act
    result = await aclient.workspace("ws").my_permission()
    # Assert
    assert route.called
    assert result.permission is WorkspacePermissionLevel.OWNER


@respx.mock
async def test_my_repository_permissions_use_the_user_path(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(
        f"{BASE_URL}/user/workspaces/ws/permissions/repositories", params={"sort": "repository.name"}
    ).mock(return_value=Response(200, json={"values": [REPO_PERMISSION]}))
    # Act
    result = [item async for item in aclient.workspace("ws").my_repository_permissions(sort="repository.name")]
    # Assert
    assert route.called
    assert result[0].permission is PermissionLevel.ADMIN


@respx.mock
async def test_user_workspaces_sends_administrator_as_a_lowercase_boolean(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/user/workspaces", params={"administrator": "true", "sort": "slug"}).mock(
        return_value=Response(
            200, json={"values": [{"type": "workspace_access", "administrator": True, "workspace": WORKSPACE_BODY}]}
        )
    )
    # Act
    result = [item async for item in aclient.user.workspaces(administrator=True, sort="slug")]
    # Assert
    assert route.called
    assert result[0].administrator is True
    assert result[0].workspace is not None
    assert result[0].workspace.slug == "ws"
