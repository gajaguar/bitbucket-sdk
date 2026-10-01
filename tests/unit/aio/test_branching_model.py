from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import respx
from httpx import Response

from bitbucket.models.branching_model import BranchTargetSettingUpdate
from bitbucket.models.branching_model import BranchingModelKind
from bitbucket.models.branching_model import BranchingModelSettingsUpdate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.aio.client import AsyncBitbucketClient

REPO: Final = f"{BASE_URL}/repositories/ws/repo"
PROJECT: Final = f"{BASE_URL}/workspaces/ws/projects/KEY"
MODEL: Final = {
    "branch_types": [{"kind": "feature", "prefix": "feature/"}, {"kind": "chore", "prefix": "chore/"}],
    "development": {"name": "main", "use_mainbranch": True},
    "production": {"name": "release", "use_mainbranch": False},
}


def _repo(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").repository("repo")


@respx.mock
async def test_repository_get_parses_branch_types_and_targets(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{REPO}/branching-model").mock(return_value=Response(200, json=MODEL))
    # Act
    result = await _repo(aclient).branching_model.get()
    # Assert
    assert route.called
    assert result.branch_types is not None
    assert [branch_type.kind for branch_type in result.branch_types] == [
        BranchingModelKind.FEATURE,
        BranchingModelKind.UNKNOWN,
    ]
    assert result.development is not None
    assert result.development.use_mainbranch is True
    assert result.production is not None
    assert result.production.name == "release"


@respx.mock
async def test_repository_effective_uses_the_effective_path(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{REPO}/effective-branching-model").mock(return_value=Response(200, json=MODEL))
    # Act
    result = await _repo(aclient).branching_model.effective()
    # Assert
    assert route.called
    assert result.development is not None
    assert result.development.name == "main"


@respx.mock
async def test_repository_settings_reads_validity(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{REPO}/branching-model/settings").mock(
        return_value=Response(
            200,
            json={
                "branch_types": [{"kind": "bugfix", "enabled": False, "prefix": ""}],
                "development": {"use_mainbranch": False, "name": "dev", "is_valid": False},
            },
        ),
    )
    # Act
    result = await _repo(aclient).branching_model.settings()
    # Assert
    assert result.branch_types is not None
    assert result.branch_types[0].enabled is False
    assert result.development is not None
    assert result.development.is_valid is False


@respx.mock
async def test_repository_update_settings_puts_the_partial_body(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{REPO}/branching-model/settings").mock(
        return_value=Response(200, json={"development": {"name": "dev", "use_mainbranch": False}}),
    )
    payload = BranchingModelSettingsUpdate(development=BranchTargetSettingUpdate(name="dev", use_mainbranch=False))
    # Act
    result = await _repo(aclient).branching_model.update_settings(payload)
    # Assert
    assert result.development is not None
    assert result.development.name == "dev"
    assert route.calls[0].request.content == b'{"development":{"name":"dev","use_mainbranch":false}}'


@respx.mock
async def test_project_get_goes_through_the_project_path(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{PROJECT}/branching-model").mock(return_value=Response(200, json=MODEL))
    # Act
    project = aclient.workspace("ws").project("KEY")
    result = await project.branching_model.get()
    # Assert
    assert project.key == "KEY"
    assert route.called
    assert result.production is not None


@respx.mock
async def test_project_settings_and_update_use_the_project_settings_path(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    get_route = respx.get(f"{PROJECT}/branching-model/settings").mock(return_value=Response(200, json={}))
    put_route = respx.put(f"{PROJECT}/branching-model/settings").mock(
        return_value=Response(200, json={"production": {"enabled": True, "use_mainbranch": True}}),
    )
    project = aclient.workspace("ws").project("KEY")
    payload = BranchingModelSettingsUpdate(production=BranchTargetSettingUpdate(enabled=True, use_mainbranch=True))
    # Act
    await project.branching_model.settings()
    result = await project.branching_model.update_settings(payload)
    # Assert
    assert get_route.called
    assert put_route.calls[0].request.content == b'{"production":{"use_mainbranch":true,"enabled":true}}'
    assert result.production is not None
    assert result.production.enabled is True
