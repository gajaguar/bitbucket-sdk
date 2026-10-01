from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import respx
from httpx import Response

from bitbucket.models.permission import ProjectPermissionLevel
from bitbucket.models.permission import ProjectPermissionUpdate
from bitbucket.models.project import ProjectCreate
from bitbucket.models.project import ProjectUpdate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.aio.client import AsyncBitbucketClient

WORKSPACE: Final = f"{BASE_URL}/workspaces/ws"
PROJECT: Final = f"{WORKSPACE}/projects/KEY"
PROJECT_BODY: Final = {"type": "project", "key": "KEY", "name": "Key", "has_publicly_visible_repos": True}
ACCOUNT: Final = {"type": "user", "account_id": "acc-1", "display_name": "Ada"}


def _project(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").project("KEY")


@respx.mock
async def test_projects_list_pages_through_the_workspace_collection(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{WORKSPACE}/projects").mock(return_value=Response(200, json={"values": [PROJECT_BODY]}))
    # Act
    result = [item async for item in aclient.workspace("ws").projects.list()]
    # Assert
    assert route.called
    assert [project.key for project in result] == ["KEY"]
    assert result[0].has_publicly_visible_repos is True


@respx.mock
async def test_projects_create_posts_the_payload(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{WORKSPACE}/projects").mock(return_value=Response(201, json=PROJECT_BODY))
    # Act
    result = await aclient.workspace("ws").projects.create(ProjectCreate(key="KEY", name="Key", is_private=True))
    # Assert
    assert route.calls.last.request.read() == b'{"key":"KEY","name":"Key","is_private":true}'
    assert result.key == "KEY"


@respx.mock
async def test_projects_get_update_delete_use_the_key_path(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    get_route = respx.get(PROJECT).mock(return_value=Response(200, json=PROJECT_BODY))
    put_route = respx.put(PROJECT).mock(return_value=Response(200, json=PROJECT_BODY))
    delete_route = respx.delete(PROJECT).mock(return_value=Response(204))
    projects = aclient.workspace("ws").projects
    # Act
    got = await projects.get("KEY")
    await projects.update("KEY", ProjectUpdate(name="Renamed"))
    await projects.delete("KEY")
    # Assert
    assert got.name == "Key"
    assert put_route.calls.last.request.read() == b'{"name":"Renamed"}'
    assert get_route.called
    assert delete_route.called


@respx.mock
async def test_project_group_permissions_round_trip(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    base = f"{PROJECT}/permissions-config/groups"
    group = {"type": "project_group_permission", "permission": "create-repo", "group": {"slug": "devs"}}
    list_route = respx.get(base).mock(return_value=Response(200, json={"values": [group]}))
    get_route = respx.get(f"{base}/devs").mock(return_value=Response(200, json=group))
    put_route = respx.put(f"{base}/devs").mock(return_value=Response(200, json=group))
    delete_route = respx.delete(f"{base}/devs").mock(return_value=Response(204))
    groups = _project(aclient).permissions.groups
    # Act
    listed = [item async for item in groups.list()]
    got = await groups.get("devs")
    await groups.update("devs", ProjectPermissionUpdate(permission=ProjectPermissionLevel.CREATE_REPO))
    await groups.delete("devs")
    # Assert
    assert list_route.called
    assert get_route.called
    assert delete_route.called
    assert listed[0].permission is ProjectPermissionLevel.CREATE_REPO
    assert got.group is not None
    assert got.group.slug == "devs"
    assert put_route.calls.last.request.read() == b'{"permission":"create-repo"}'


@respx.mock
async def test_project_user_permissions_use_the_selected_user_id_path(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    base = f"{PROJECT}/permissions-config/users"
    user = {"type": "project_user_permission", "permission": "surprise", "user": ACCOUNT}
    list_route = respx.get(base).mock(return_value=Response(200, json={"values": [user]}))
    get_route = respx.get(f"{base}/acc-1").mock(return_value=Response(200, json=user))
    put_route = respx.put(f"{base}/acc-1").mock(return_value=Response(200, json=user))
    delete_route = respx.delete(f"{base}/acc-1").mock(return_value=Response(204))
    users = _project(aclient).permissions.users
    # Act
    listed = [item async for item in users.list()]
    got = await users.get("acc-1")
    await users.update("acc-1", ProjectPermissionUpdate(permission=ProjectPermissionLevel.ADMIN))
    await users.delete("acc-1")
    # Assert
    assert list_route.called
    assert get_route.called
    assert delete_route.called
    assert listed[0].permission is ProjectPermissionLevel.UNKNOWN
    assert got.user is not None
    assert got.user.account_id == "acc-1"
    assert put_route.calls.last.request.read() == b'{"permission":"admin"}'


@respx.mock
async def test_project_default_reviewers_parse_the_wrapper_and_use_the_user_path(
    aclient: AsyncBitbucketClient,
) -> None:
    # Arrange
    base = f"{PROJECT}/default-reviewers"
    wrapper = {"type": "default_reviewer", "reviewer_type": "project", "user": ACCOUNT}
    list_route = respx.get(base).mock(return_value=Response(200, json={"values": [wrapper]}))
    get_route = respx.get(f"{base}/acc-1").mock(return_value=Response(200, json=ACCOUNT))
    put_route = respx.put(f"{base}/acc-1").mock(return_value=Response(200, json=ACCOUNT))
    delete_route = respx.delete(f"{base}/acc-1").mock(return_value=Response(204))
    reviewers = _project(aclient).default_reviewers
    # Act
    listed = [item async for item in reviewers.list()]
    got = await reviewers.get("acc-1")
    added = await reviewers.add("acc-1")
    await reviewers.remove("acc-1")
    # Assert
    assert list_route.called
    assert get_route.called
    assert put_route.called
    assert delete_route.called
    assert listed[0].reviewer_type == "project"
    assert listed[0].user is not None
    assert listed[0].user.display_name == "Ada"
    assert got.display_name == "Ada"
    assert added.account_id == "acc-1"
