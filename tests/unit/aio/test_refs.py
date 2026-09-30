from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

from bitbucket.models.branch import BranchCreate
from bitbucket.models.branch import RefTargetSpec
from bitbucket.models.tag import TagCreate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.aio.client import AsyncBitbucketClient


def _refs(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").repository("repo").refs


@respx.mock
async def test_refs_list_returns_combined_branches_and_tags(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/refs").mock(
        return_value=Response(200, json={"values": [{"name": "main", "type": "branch"}], "next": None}),
    )
    # Act
    refs = [item async for item in _refs(aclient).list()]
    # Assert
    assert [ref.name for ref in refs] == ["main"]


@respx.mock
async def test_branch_create_posts_name_and_target_hash(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/refs/branches").mock(
        return_value=Response(200, json={"name": "feature"}),
    )
    payload = BranchCreate(name="feature", target=RefTargetSpec(hash="abc123"))
    # Act
    result = await _refs(aclient).branches.create(payload)
    # Assert
    assert result.name == "feature"
    assert route.calls[0].request.content == b'{"name":"feature","target":{"hash":"abc123"}}'


@respx.mock
async def test_branch_get_returns_branch(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/refs/branches/main").mock(
        return_value=Response(200, json={"name": "main"}),
    )
    # Act
    result = await _refs(aclient).branches.get("main")
    # Assert
    assert result.name == "main"


@respx.mock
async def test_branch_list_returns_branches(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/refs/branches").mock(
        return_value=Response(200, json={"values": [{"name": "main"}], "next": None}),
    )
    # Act
    branches = [item async for item in _refs(aclient).branches.list()]
    # Assert
    assert [branch.name for branch in branches] == ["main"]


@respx.mock
async def test_branch_delete_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/refs/branches/feature").mock(
        return_value=Response(204),
    )
    # Act
    result = await _refs(aclient).branches.delete("feature")
    # Assert
    assert result is None
    assert route.called


@respx.mock
async def test_tag_create_posts_name_target_and_message(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/refs/tags").mock(
        return_value=Response(200, json={"name": "v1.0"}),
    )
    payload = TagCreate(name="v1.0", target=RefTargetSpec(hash="abc123"), message="Release 1.0")
    # Act
    result = await _refs(aclient).tags.create(payload)
    # Assert
    assert result.name == "v1.0"
    assert route.calls[0].request.content == (b'{"name":"v1.0","target":{"hash":"abc123"},"message":"Release 1.0"}')


@respx.mock
async def test_tag_get_returns_tag(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/refs/tags/v1.0").mock(
        return_value=Response(200, json={"name": "v1.0"}),
    )
    # Act
    result = await _refs(aclient).tags.get("v1.0")
    # Assert
    assert result.name == "v1.0"


@respx.mock
async def test_tag_list_returns_tags(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/refs/tags").mock(
        return_value=Response(200, json={"values": [{"name": "v1.0"}], "next": None}),
    )
    # Act
    tags = [item async for item in _refs(aclient).tags.list()]
    # Assert
    assert [tag.name for tag in tags] == ["v1.0"]


@respx.mock
async def test_tag_delete_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/refs/tags/v1.0").mock(return_value=Response(204))
    # Act
    result = await _refs(aclient).tags.delete("v1.0")
    # Assert
    assert result is None
    assert route.called
