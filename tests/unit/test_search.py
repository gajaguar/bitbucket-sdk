from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import pytest
import respx
from httpx import Response

from bitbucket.errors import NotFoundError
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient

WORKSPACE_SEARCH: Final = f"{BASE_URL}/workspaces/acme/search/code"
USER_SEARCH: Final = f"{BASE_URL}/users/acc-1/search/code"
TEAM_SEARCH: Final = f"{BASE_URL}/teams/acme-team/search/code"
RESULT_BODY: Final = {
    "type": "code_search_result",
    "content_match_count": 2,
    "content_matches": [
        {
            "lines": [
                {"line": 2, "segments": []},
                {"line": 3, "segments": [{"text": "def "}, {"text": "foo", "match": True}, {"text": "():"}]},
            ]
        }
    ],
    "path_matches": [{"text": "src/"}, {"text": "foo", "match": True}, {"text": ".py"}],
    "file": {"path": "src/foo.py", "type": "commit_file"},
}


@respx.mock
def test_workspace_search_sends_the_query(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(WORKSPACE_SEARCH, params={"search_query": "foo repo:demo"}).mock(
        return_value=Response(200, json={"size": 1, "values": [RESULT_BODY]})
    )
    # Act
    result = list(client.workspace("acme").search.code("foo repo:demo"))
    # Assert
    assert route.called
    assert dict(route.calls.last.request.url.params) == {"search_query": "foo repo:demo"}
    assert [item.file.path for item in result if item.file] == ["src/foo.py"]


@respx.mock
def test_user_search_sends_fields_and_pagelen(client: BitbucketClient) -> None:
    # Arrange
    params = {"search_query": "foo", "fields": "+values.file.commit.repository", "pagelen": "50"}
    route = respx.get(USER_SEARCH, params=params).mock(return_value=Response(200, json={"values": [RESULT_BODY]}))
    # Act
    list(client.users("acc-1").search.code("foo", fields="+values.file.commit.repository", pagelen=50))
    # Assert
    assert route.called


@respx.mock
def test_team_search_uses_the_teams_path(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(TEAM_SEARCH, params={"search_query": "foo"}).mock(
        return_value=Response(200, json={"values": [RESULT_BODY]})
    )
    # Act
    page = client.teams("acme-team").search.code_page("foo")
    # Assert
    assert route.called
    assert len(page.items) == 1


@respx.mock
def test_search_code_follows_the_next_link(client: BitbucketClient) -> None:
    # Arrange
    next_url = f"{WORKSPACE_SEARCH}?search_query=foo&page=2"
    second = respx.get(WORKSPACE_SEARCH, params={"search_query": "foo", "page": "2"}).mock(
        return_value=Response(200, json={"values": [{**RESULT_BODY, "content_match_count": 5}]})
    )
    respx.get(WORKSPACE_SEARCH, params={"search_query": "foo"}).mock(
        return_value=Response(200, json={"values": [RESULT_BODY], "next": next_url})
    )
    # Act
    result = list(client.workspace("acme").search.code("foo", pagelen=1))
    # Assert
    assert [item.content_match_count for item in result] == [2, 5]
    assert "pagelen" not in second.calls.last.request.url.params


@respx.mock
def test_search_code_page_parses_the_nested_matches(client: BitbucketClient) -> None:
    # Arrange
    respx.get(WORKSPACE_SEARCH).mock(
        return_value=Response(200, json={"size": 7, "query_substituted": False, "values": [RESULT_BODY]})
    )
    # Act
    page = client.workspace("acme").search.code_page("foo")
    # Assert
    item = page.items[0]
    assert page.size == 7
    assert page.next_cursor is None
    assert item.content_matches is not None
    assert item.content_matches[0].lines is not None
    segments = item.content_matches[0].lines[1].segments or []
    assert [segment.text for segment in segments if segment.match] == ["foo"]
    assert [segment.match for segment in item.path_matches or []] == [None, True, None]


@respx.mock
def test_search_raises_not_found_when_search_is_disabled(client: BitbucketClient) -> None:
    # Arrange
    respx.get(WORKSPACE_SEARCH).mock(
        return_value=Response(404, json={"type": "error", "error": {"message": "Search is not enabled"}})
    )
    # Act
    # Assert
    with pytest.raises(NotFoundError):
        client.workspace("acme").search.code_page("foo")
