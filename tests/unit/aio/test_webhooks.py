from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import respx
from httpx import Response

from bitbucket.errors import NotFoundError
from bitbucket.models.hook import WebhookCreate
from bitbucket.models.hook import WebhookUpdate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.aio.client import AsyncBitbucketClient


def _workspace(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws")


@respx.mock
async def test_hook_events_subject_types_maps_each_subject_to_its_events_link(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/hook_events").mock(
        return_value=Response(
            200,
            json={
                "repository": {"links": {"events": {"href": f"{BASE_URL}/hook_events/repository"}}},
                "workspace": {"links": {"events": {"href": f"{BASE_URL}/hook_events/workspace"}}},
            },
        ),
    )
    # Act
    subject_types = await aclient.hook_events.subject_types()
    # Assert
    assert route.called
    assert sorted(subject_types) == ["repository", "workspace"]
    workspace_links = subject_types["workspace"].links
    assert workspace_links is not None
    assert workspace_links.events is not None
    assert workspace_links.events.href == f"{BASE_URL}/hook_events/workspace"


@respx.mock
async def test_hook_events_list_follows_next_cursor_across_pages(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    next_url = f"{BASE_URL}/hook_events/workspace?page=2"
    route = respx.get(f"{BASE_URL}/hook_events/workspace").mock(
        side_effect=[
            Response(
                200,
                json={"values": [{"event": "repo:push", "category": "Repository", "label": "Push"}], "next": next_url},
            ),
            Response(200, json={"values": [{"event": "pullrequest:approved"}], "next": None}),
        ],
    )
    # Act
    events = [event async for event in aclient.hook_events.list("workspace")]
    # Assert
    assert [event.event for event in events] == ["repo:push", "pullrequest:approved"]
    assert events[0].category == "Repository"
    assert [str(call.request.url) for call in route.calls] == [f"{BASE_URL}/hook_events/workspace", next_url]


@respx.mock
async def test_hook_events_list_page_requests_the_cursor_url_verbatim(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    cursor = f"{BASE_URL}/hook_events/repository?page=3"
    route = respx.get(cursor).mock(return_value=Response(200, json={"values": [], "next": None}))
    # Act
    page = await aclient.hook_events.list_page("repository", cursor=cursor)
    # Assert
    assert route.called
    assert page.items == []
    assert page.next_cursor is None


@respx.mock
async def test_hook_events_list_raises_not_found_for_an_invalid_subject_type(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/hook_events/team").mock(
        return_value=Response(404, json={"type": "error", "error": {"message": "Not found"}}),
    )
    # Act
    # Assert
    with pytest.raises(NotFoundError):
        [event async for event in aclient.hook_events.list("team")]


@respx.mock
async def test_workspace_hook_create_posts_url_and_events(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/workspaces/ws/hooks").mock(
        return_value=Response(201, json={"uuid": "{h}"}),
    )
    payload = WebhookCreate(description="ci", url="https://ci.example.com/hook", events=["repo:push"])
    # Act
    result = await _workspace(aclient).hooks.create(payload)
    # Assert
    assert result.uuid == "{h}"
    assert route.calls[0].request.content == (
        b'{"description":"ci","url":"https://ci.example.com/hook","events":["repo:push"]}'
    )


@respx.mock
async def test_workspace_hook_list_returns_configured_hooks(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/workspaces/ws/hooks").mock(
        return_value=Response(200, json={"values": [{"uuid": "{h}"}], "next": None}),
    )
    # Act
    hooks = [item async for item in _workspace(aclient).hooks.list()]
    # Assert
    assert [hook.uuid for hook in hooks] == ["{h}"]


@respx.mock
async def test_workspace_hook_get_returns_the_hook(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/workspaces/ws/hooks/{{h}}").mock(
        return_value=Response(200, json={"uuid": "{h}", "active": True}),
    )
    # Act
    result = await _workspace(aclient).hooks.get("{h}")
    # Assert
    assert route.called
    assert result.uuid == "{h}"
    assert result.active is True


@respx.mock
async def test_workspace_hook_update_puts_new_url(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/workspaces/ws/hooks/{{h}}").mock(
        return_value=Response(200, json={"uuid": "{h}", "url": "https://new.example.com"}),
    )
    # Act
    result = await _workspace(aclient).hooks.update("{h}", WebhookUpdate(url="https://new.example.com"))
    # Assert
    assert result.url == "https://new.example.com"
    assert route.calls[0].request.content == b'{"url":"https://new.example.com"}'


@respx.mock
async def test_workspace_hook_delete_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/workspaces/ws/hooks/{{h}}").mock(return_value=Response(204))
    # Act
    result = await _workspace(aclient).hooks.delete("{h}")
    # Assert
    assert result is None
    assert route.called
