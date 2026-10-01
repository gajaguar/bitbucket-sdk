from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import respx
from httpx import Response

from bitbucket.models.branch_restriction import BranchMatchKind
from bitbucket.models.branch_restriction import BranchRestrictionCreate
from bitbucket.models.branch_restriction import BranchRestrictionKind
from bitbucket.models.branch_restriction import BranchRestrictionUpdate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient

PATH: Final = f"{BASE_URL}/repositories/ws/repo/branch-restrictions"


def _repo(client: BitbucketClient):
    return client.workspace("ws").repository("repo")


@respx.mock
def test_list_sends_kind_and_pattern_and_follows_next_cursor(client: BitbucketClient) -> None:
    # Arrange
    next_url = f"{PATH}?page=2"
    route = respx.get(PATH).mock(
        side_effect=[
            Response(200, json={"values": [{"id": 1, "kind": "push"}], "next": next_url}),
            Response(200, json={"values": [{"id": 2, "kind": "force"}], "next": None}),
        ],
    )
    # Act
    restrictions = list(_repo(client).branch_restrictions.list(kind="push", pattern="main"))
    # Assert
    assert [restriction.id for restriction in restrictions] == [1, 2]
    assert route.calls[0].request.url.params["kind"] == "push"
    assert route.calls[0].request.url.params["pattern"] == "main"
    assert str(route.calls[1].request.url) == next_url


@respx.mock
def test_get_parses_the_restriction(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{PATH}/7").mock(
        return_value=Response(
            200,
            json={
                "id": 7,
                "kind": "require_approvals_to_merge",
                "branch_match_kind": "branching_model",
                "branch_type": "production",
                "value": 2,
                "users": [{"uuid": "{u}"}],
                "groups": [{"slug": "devs"}],
            },
        ),
    )
    # Act
    result = _repo(client).branch_restrictions.get(7)
    # Assert
    assert result.kind is BranchRestrictionKind.REQUIRE_APPROVALS_TO_MERGE
    assert result.branch_match_kind is BranchMatchKind.BRANCHING_MODEL
    assert result.value == 2
    assert result.users is not None
    assert result.users[0].uuid == "{u}"
    assert result.groups is not None
    assert result.groups[0].slug == "devs"


@respx.mock
def test_get_maps_an_unknown_kind_to_unknown(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{PATH}/8").mock(return_value=Response(200, json={"id": 8, "kind": "brand_new_kind"}))
    # Act
    result = _repo(client).branch_restrictions.get(8)
    # Assert
    assert result.kind is BranchRestrictionKind.UNKNOWN


@respx.mock
def test_create_posts_only_the_set_fields(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(PATH).mock(return_value=Response(201, json={"id": 3, "kind": "push"}))
    payload = BranchRestrictionCreate(kind=BranchRestrictionKind.PUSH, pattern="main")
    # Act
    result = _repo(client).branch_restrictions.create(payload)
    # Assert
    assert result.id == 3
    assert route.calls[0].request.content == b'{"kind":"push","pattern":"main"}'


@respx.mock
def test_update_puts_the_partial_body(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{PATH}/3").mock(return_value=Response(200, json={"id": 3, "value": 4}))
    # Act
    result = _repo(client).branch_restrictions.update(3, BranchRestrictionUpdate(value=4))
    # Assert
    assert result.value == 4
    assert route.calls[0].request.content == b'{"value":4}'


@respx.mock
def test_delete_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{PATH}/3").mock(return_value=Response(204))
    # Act
    result = _repo(client).branch_restrictions.delete(3)
    # Assert
    assert result is None
    assert route.called
