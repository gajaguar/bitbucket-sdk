from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import pytest
import respx
from httpx import Response

from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.aio.client import AsyncBitbucketClient

# Every paginated iterator has a public *_page method that takes the next URL as `cursor`.
CASES: Final = [
    pytest.param(
        lambda c, cur: _repo(c).commits.diffstat_page("a..b", cursor=cur),
        "GET",
        "/repositories/ws/repo/diffstat/a..b",
        {"lines_added": 2},
        id="commits-diffstat",
    ),
    pytest.param(
        lambda c, cur: _repo(c).commits.list_from_page("main", cursor=cur),
        "GET",
        "/repositories/ws/repo/commits/main",
        {"hash": "a1"},
        id="commits-list-from",
    ),
    pytest.param(
        lambda c, cur: _repo(c).commits.file_conflicts_page("a..b", cursor=cur),
        "GET",
        "/repositories/ws/repo/file-conflicts/a..b",
        {"path": "a.py"},
        id="commits-file-conflicts",
    ),
    pytest.param(
        lambda c, cur: _repo(c).commits.list_by_post_page(cursor=cur, include=["main"]),
        "POST",
        "/repositories/ws/repo/commits",
        {"hash": "a1"},
        id="commits-list-by-post",
    ),
    pytest.param(
        lambda c, cur: _repo(c).commits.list_from_by_post_page("main", cursor=cur),
        "POST",
        "/repositories/ws/repo/commits/main",
        {"hash": "a1"},
        id="commits-list-from-by-post",
    ),
    pytest.param(
        lambda c, cur: _repo(c).pull_requests.activity_page(5, cursor=cur),
        "GET",
        "/repositories/ws/repo/pullrequests/5/activity",
        {"update": {"state": "OPEN"}},
        id="pull-requests-activity",
    ),
    pytest.param(
        lambda c, cur: _repo(c).pull_requests.commits_page(5, cursor=cur),
        "GET",
        "/repositories/ws/repo/pullrequests/5/commits",
        {"hash": "a1"},
        id="pull-requests-commits",
    ),
    pytest.param(
        lambda c, cur: _repo(c).pull_requests.conflicts_page(5, cursor=cur),
        "GET",
        "/repositories/ws/repo/pullrequests/5/conflicts",
        {"path": "a.py"},
        id="pull-requests-conflicts",
    ),
    pytest.param(
        lambda c, cur: _repo(c).pull_requests.diffstat_page(5, cursor=cur),
        "GET",
        "/repositories/ws/repo/pullrequests/5/diffstat",
        {"lines_added": 2},
        id="pull-requests-diffstat",
    ),
    pytest.param(
        lambda c, cur: c.workspace("ws").repositories.forks_page("repo", cursor=cur),
        "GET",
        "/repositories/ws/repo/forks",
        {"name": "fork-1"},
        id="repositories-forks",
    ),
    pytest.param(
        lambda c, cur: c.workspace("ws").repositories.watchers_page("repo", cursor=cur),
        "GET",
        "/repositories/ws/repo/watchers",
        {"uuid": "{x}"},
        id="repositories-watchers",
    ),
    pytest.param(
        lambda c, cur: c.workspace("ws").repositories.commit_pull_requests_page("repo", "abc", cursor=cur),
        "GET",
        "/repositories/ws/repo/commit/abc/pullrequests",
        {"id": 9},
        id="repositories-commit-pull-requests",
    ),
    pytest.param(
        lambda c, cur: c.workspace("ws").repositories.pull_request_activity_page("repo", cursor=cur),
        "GET",
        "/repositories/ws/repo/pullrequests/activity",
        {"update": {"state": "MERGED"}},
        id="repositories-pull-request-activity",
    ),
    pytest.param(
        lambda c, cur: _repo(c).source.file_history_page("abc", "README.md", cursor=cur),
        "GET",
        "/repositories/ws/repo/filehistory/abc/README.md",
        {"path": "README.md"},
        id="source-file-history",
    ),
    pytest.param(
        lambda c, cur: _repo(c).source.list_path_page("abc", "src", cursor=cur),
        "GET",
        "/repositories/ws/repo/src/abc/src",
        {"path": "src/main.py"},
        id="source-list-path",
    ),
    pytest.param(
        lambda c, cur: c.workspace("ws").pull_requests_by_author_page("alice", cursor=cur),
        "GET",
        "/workspaces/ws/pullrequests/alice",
        {"id": 1},
        id="workspace-pull-requests-by-author",
    ),
    pytest.param(
        lambda c, cur: c.workspace("ws").snippet("abc").commits_page(cursor=cur),
        "GET",
        "/snippets/ws/abc/commits",
        {"hash": "367ab19"},
        id="snippet-commits",
    ),
    pytest.param(
        lambda c, cur: c.workspace("ws").snippet("abc").watchers_page(cursor=cur),
        "GET",
        "/snippets/ws/abc/watchers",
        {"display_name": "Ann"},
        id="snippet-watchers",
    ),
]


def _repo(c):
    return c.workspace("ws").repository("repo")


@pytest.mark.parametrize(("call", "method", "path", "item"), CASES)
@respx.mock
async def test_page_method_returns_the_items_and_the_next_cursor(
    aclient: AsyncBitbucketClient, call, method, path, item
) -> None:
    # Arrange
    next_url = f"{BASE_URL}{path}?page=2"
    respx.route(method=method, url=f"{BASE_URL}{path}").mock(
        return_value=Response(200, json={"values": [item], "next": next_url}),
    )
    # Act
    page = await call(aclient, None)
    # Assert
    assert (len(page.items), page.next_cursor) == (1, next_url)


@pytest.mark.parametrize(("call", "method", "path", "item"), CASES)
@respx.mock
async def test_page_method_requests_the_cursor_url_it_is_given(
    aclient: AsyncBitbucketClient, call, method, path, item
) -> None:
    # Arrange
    cursor = f"{BASE_URL}{path}?page=2"
    route = respx.route(method=method, url=cursor).mock(return_value=Response(200, json={"values": [item]}))
    # Act
    page = await call(aclient, cursor)
    # Assert
    assert (route.call_count, len(page.items), page.next_cursor) == (1, 1, None)
