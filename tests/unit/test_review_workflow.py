from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import respx
from httpx import Response

from bitbucket.errors import NotFoundError
from bitbucket.errors import ServerError
from bitbucket.errors import TransportError
from bitbucket.models.comment import CommentContentCreate
from bitbucket.models.comment import CommentCreate
from bitbucket.models.comment import CommentUpdate
from bitbucket.models.pull_request import BranchSpec
from bitbucket.models.pull_request import EndpointSpec
from bitbucket.models.pull_request import PullRequestCreate
from bitbucket.models.pull_request import PullRequestUpdate
from bitbucket.models.status import CommitStatusCreate
from bitbucket.models.status import CommitStatusUpdate
from bitbucket.models.task import TaskContentCreate
from bitbucket.models.task import TaskCreate
from bitbucket.models.task import TaskUpdate
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient


def _pull_requests(client: BitbucketClient):
    return client.workspace("ws").repository("repo").pull_requests


def _comments(client: BitbucketClient):
    return _pull_requests(client).comments(5)


def _tasks(client: BitbucketClient):
    return _pull_requests(client).tasks(5)


def _repository(client: BitbucketClient):
    return client.workspace("ws").repository("repo")


@respx.mock
def test_pull_request_list_filters_by_state_and_query(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(
        return_value=Response(200, json={"values": [{"id": 1, "title": "Fix bug", "state": "OPEN"}], "next": None}),
    )
    # Act
    pull_requests = list(_pull_requests(client).list(state="OPEN", q='title~"fix"'))
    # Assert
    assert [pr.id for pr in pull_requests] == [1]
    assert dict(route.calls[0].request.url.params) == {"state": "OPEN", "q": 'title~"fix"'}


# respx matches routes in registration order, so the page-2 route (filtered on
# params) must be registered first — otherwise the unfiltered first-page route
# would also catch the page-2 request and loop forever.
@respx.mock
def test_pull_request_list_follows_next_cursor_across_pages(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests", params={"page": "2"}).mock(
        return_value=Response(200, json={"values": [{"id": 2}], "next": None}),
    )
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(
        return_value=Response(
            200,
            json={"values": [{"id": 1}], "next": f"{BASE_URL}/repositories/ws/repo/pullrequests?page=2"},
        ),
    )
    # Act
    pull_requests = list(_pull_requests(client).list())
    # Assert
    assert [pr.id for pr in pull_requests] == [1, 2]


@respx.mock
def test_pull_request_get_returns_pull_request(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/42").mock(
        return_value=Response(200, json={"id": 42, "title": "Fix bug"}),
    )
    # Act
    pull_request = _pull_requests(client).get(42)
    # Assert
    assert pull_request.id == 42
    assert pull_request.title == "Fix bug"


@respx.mock
def test_pull_request_get_raises_not_found_for_unknown_id(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/42").mock(
        return_value=Response(404, json={"error": {"message": "nope"}}),
    )
    # Act
    with pytest.raises(NotFoundError) as exc_info:
        _pull_requests(client).get(42)
    # Assert
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "nope"


@respx.mock
def test_pull_request_get_raises_transport_error_for_invalid_json_body(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/42").mock(
        return_value=Response(200, content=b"not json", headers={"content-type": "application/json"}),
    )
    # Act
    # Assert
    with pytest.raises(TransportError, match="Invalid JSON"):
        _pull_requests(client).get(42)


@respx.mock
def test_pull_request_diff_returns_raw_text(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/diff").mock(
        return_value=Response(200, text="diff --git a b"),
    )
    # Act
    diff = _pull_requests(client).diff(5)
    # Assert
    assert diff == "diff --git a b"


@respx.mock
def test_pull_request_diff_raises_not_found_for_unknown_id(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/diff").mock(
        return_value=Response(404, json={"error": {"message": "nope"}}),
    )
    # Act
    with pytest.raises(NotFoundError) as exc_info:
        _pull_requests(client).diff(5)
    # Assert
    assert exc_info.value.status_code == 404


@respx.mock
def test_pull_request_statuses_list_returns_build_statuses(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/statuses").mock(
        return_value=Response(200, json={"values": [{"key": "build", "state": "SUCCESSFUL"}], "next": None}),
    )
    # Act
    statuses = list(_pull_requests(client).statuses(5).list())
    # Assert
    assert [status.key for status in statuses] == ["build"]
    assert [status.state for status in statuses] == ["SUCCESSFUL"]


@respx.mock
def test_pull_request_comment_create_posts_content_payload(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments").mock(
        return_value=Response(200, json={"id": 99}),
    )
    payload = CommentCreate(content=CommentContentCreate(raw="nice"))
    # Act
    result = _comments(client).create(payload)
    # Assert
    assert result.id == 99
    assert route.calls[0].request.content == b'{"content":{"raw":"nice"}}'


@respx.mock
def test_pull_request_comment_list_sorts_by_created_on(client: BitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments").mock(
        return_value=Response(200, json={"values": [{"id": 1}], "next": None}),
    )
    # Act
    comments = list(_comments(client).list(sort="-created_on"))
    # Assert
    assert [comment.id for comment in comments] == [1]
    assert dict(route.calls[0].request.url.params) == {"sort": "-created_on"}


@respx.mock
def test_pull_request_comment_get_returns_comment(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments/9").mock(
        return_value=Response(200, json={"id": 9}),
    )
    # Act
    comment = _comments(client).get(9)
    # Assert
    assert comment.id == 9


@respx.mock
def test_pull_request_comment_update_puts_edited_content(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments/9").mock(
        return_value=Response(200, json={"id": 9}),
    )
    # Act
    result = _comments(client).update(9, CommentUpdate(content=CommentContentCreate(raw="edited")))
    # Assert
    assert result.id == 9
    assert route.calls[0].request.content == b'{"content":{"raw":"edited"}}'


@respx.mock
def test_pull_request_comment_delete_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments/9").mock(
        return_value=Response(204),
    )
    # Act
    result = _comments(client).delete(9)
    # Assert
    assert result is None
    assert route.called


@respx.mock
def test_pull_request_approve_returns_approving_account(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/approve").mock(
        return_value=Response(200, json={"uuid": "{abc}"}),
    )
    # Act
    result = _pull_requests(client).approve(5)
    # Assert
    assert result.uuid == "{abc}"
    assert route.calls[0].request.content == b""


@respx.mock
def test_pull_request_approve_raises_server_error_on_upstream_failure(client: BitbucketClient) -> None:
    # Arrange
    respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/approve").mock(
        return_value=Response(500, text="boom"),
    )
    # Act
    with pytest.raises(ServerError) as exc_info:
        _pull_requests(client).approve(5)
    # Assert
    assert exc_info.value.status_code == 500
    assert exc_info.value.raw == "boom"


@respx.mock
def test_pull_request_create_posts_title_and_source_branch(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(
        return_value=Response(200, json={"id": 7, "title": "New PR"}),
    )
    payload = PullRequestCreate(title="New PR", source=EndpointSpec(branch=BranchSpec(name="feature")))
    # Act
    result = _pull_requests(client).create(payload)
    # Assert
    assert result.id == 7
    assert route.calls[0].request.content == b'{"title":"New PR","source":{"branch":{"name":"feature"}}}'


@respx.mock
def test_pull_request_update_puts_only_the_changed_title(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/pullrequests/5").mock(
        return_value=Response(200, json={"id": 5, "title": "Renamed"}),
    )
    # Act
    result = _pull_requests(client).update(5, PullRequestUpdate(title="Renamed"))
    # Assert
    assert result.title == "Renamed"
    assert route.calls[0].request.content == b'{"title":"Renamed"}'


@respx.mock
def test_pull_request_commits_returns_commit_hashes(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/commits").mock(
        return_value=Response(200, json={"values": [{"hash": "abc123"}], "next": None}),
    )
    # Act
    commits = list(_pull_requests(client).commits(5))
    # Assert
    assert [commit.hash for commit in commits] == ["abc123"]


@respx.mock
def test_pull_request_conflicts_returns_conflicting_files(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/conflicts").mock(
        return_value=Response(200, json={"values": [{"path": "a.py"}], "next": None}),
    )
    # Act
    conflicts = list(_pull_requests(client).conflicts(5))
    # Assert
    assert [conflict.path for conflict in conflicts] == ["a.py"]


@respx.mock
def test_pull_request_diffstat_returns_line_counts(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/diffstat").mock(
        return_value=Response(200, json={"values": [{"lines_added": 3, "lines_removed": 1}], "next": None}),
    )
    # Act
    stats = list(_pull_requests(client).diffstat(5))
    # Assert
    assert [stat.lines_added for stat in stats] == [3]


@respx.mock
def test_pull_request_mbox_format_export_returns_raw_text(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/patch").mock(
        return_value=Response(200, text="From abc123"),
    )
    # Act
    result = _pull_requests(client).patch(5)
    # Assert
    assert result == "From abc123"


@respx.mock
def test_pull_request_activity_returns_activity_feed(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/activity").mock(
        return_value=Response(200, json={"values": [{"update": {"state": "OPEN"}}], "next": None}),
    )
    # Act
    activity = list(_pull_requests(client).activity(5))
    # Assert
    assert [entry.update.state for entry in activity] == ["OPEN"]


@respx.mock
def test_repository_pull_request_activity_returns_repo_wide_feed(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/activity").mock(
        return_value=Response(200, json={"values": [{"update": {"state": "MERGED"}}], "next": None}),
    )
    # Act
    activity = list(client.workspace("ws").repositories.pull_request_activity("repo"))
    # Assert
    assert [entry.update.state for entry in activity] == ["MERGED"]


@respx.mock
def test_repository_commit_pull_requests_returns_prs_containing_commit(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/commit/abc123/pullrequests").mock(
        return_value=Response(200, json={"values": [{"id": 9}], "next": None}),
    )
    # Act
    pull_requests = list(client.workspace("ws").repositories.commit_pull_requests("repo", "abc123"))
    # Assert
    assert [pr.id for pr in pull_requests] == [9]


@respx.mock
def test_pull_request_task_create_posts_content_payload(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/tasks").mock(
        return_value=Response(200, json={"id": 1}),
    )
    payload = TaskCreate(content=TaskContentCreate(raw="fix this"))
    # Act
    result = _tasks(client).create(payload)
    # Assert
    assert result.id == 1
    assert route.calls[0].request.content == b'{"content":{"raw":"fix this"}}'


@respx.mock
def test_pull_request_task_list_returns_tasks(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/tasks").mock(
        return_value=Response(200, json={"values": [{"id": 1, "state": "UNRESOLVED"}], "next": None}),
    )
    # Act
    tasks = list(_tasks(client).list())
    # Assert
    assert [task.state for task in tasks] == ["UNRESOLVED"]


@respx.mock
def test_pull_request_task_update_puts_resolved_state(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/tasks/1").mock(
        return_value=Response(200, json={"id": 1, "state": "RESOLVED"}),
    )
    # Act
    result = _tasks(client).update(1, TaskUpdate(state="RESOLVED"))
    # Assert
    assert result.state == "RESOLVED"
    assert route.calls[0].request.content == b'{"state":"RESOLVED"}'


@respx.mock
def test_pull_request_task_delete_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/tasks/1").mock(
        return_value=Response(204),
    )
    # Act
    result = _tasks(client).delete(1)
    # Assert
    assert result is None
    assert route.called


@respx.mock
def test_pull_request_comment_resolve_returns_resolved_comment(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments/9/resolve").mock(
        return_value=Response(200, json={"id": 9, "pending": False}),
    )
    # Act
    result = _comments(client).resolve(9)
    # Assert
    assert result.id == 9
    assert route.calls[0].request.content == b""


@respx.mock
def test_pull_request_comment_unresolve_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments/9/resolve").mock(
        return_value=Response(204),
    )
    # Act
    result = _comments(client).unresolve(9)
    # Assert
    assert result is None
    assert route.called


@respx.mock
def test_pull_request_properties_get_returns_stored_value(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/properties/my-app/state").mock(
        return_value=Response(200, json={"stage": "review"}),
    )
    # Act
    value = _pull_requests(client).properties(5).get("my-app", "state")
    # Assert
    assert value == {"stage": "review"}


@respx.mock
def test_pull_request_properties_put_sends_value_as_body(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/properties/my-app/state").mock(
        return_value=Response(200, json={"stage": "done"}),
    )
    # Act
    result = _pull_requests(client).properties(5).put("my-app", "state", {"stage": "done"})
    # Assert
    assert result == {"stage": "done"}
    assert route.calls[0].request.content == b'{"stage":"done"}'


@respx.mock
def test_pull_request_properties_delete_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/properties/my-app/state").mock(
        return_value=Response(204),
    )
    # Act
    result = _pull_requests(client).properties(5).delete("my-app", "state")
    # Assert
    assert result is None
    assert route.called


@respx.mock
def test_default_reviewer_get_returns_reviewer(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/default-reviewers/alice").mock(
        return_value=Response(200, json={"uuid": "{x}"}),
    )
    # Act
    reviewer = _repository(client).default_reviewers.get("alice")
    # Assert
    assert reviewer.uuid == "{x}"


@respx.mock
def test_default_reviewer_add_puts_target_username(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/default-reviewers/alice").mock(
        return_value=Response(200, json={"uuid": "{x}"}),
    )
    # Act
    reviewer = _repository(client).default_reviewers.add("alice")
    # Assert
    assert reviewer.uuid == "{x}"
    assert route.called


@respx.mock
def test_default_reviewer_remove_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/default-reviewers/alice").mock(
        return_value=Response(204),
    )
    # Act
    result = _repository(client).default_reviewers.remove("alice")
    # Assert
    assert result is None
    assert route.called


@respx.mock
def test_default_reviewer_effective_returns_repo_and_project_reviewers(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/effective-default-reviewers").mock(
        return_value=Response(200, json={"values": [{"uuid": "{x}", "reviewer_type": "project"}], "next": None}),
    )
    # Act
    reviewers = list(_repository(client).default_reviewers.effective())
    # Assert
    assert [reviewer.reviewer_type for reviewer in reviewers] == ["project"]


@respx.mock
def test_commit_status_list_returns_build_statuses(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/commit/abc123/statuses").mock(
        return_value=Response(200, json={"values": [{"key": "build"}], "next": None}),
    )
    # Act
    statuses = list(_repository(client).commit_statuses.list("abc123"))
    # Assert
    assert [status.key for status in statuses] == ["build"]


@respx.mock
def test_commit_status_create_posts_build_status(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/commit/abc123/statuses/build").mock(
        return_value=Response(200, json={"key": "build", "state": "INPROGRESS"}),
    )
    payload = CommitStatusCreate(key="build", state="INPROGRESS", url="https://ci.example.com/1")
    # Act
    result = _repository(client).commit_statuses.create("abc123", payload)
    # Assert
    assert result.state == "INPROGRESS"
    assert route.calls[0].request.content == (b'{"key":"build","state":"INPROGRESS","url":"https://ci.example.com/1"}')


@respx.mock
def test_commit_status_get_returns_build_status(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/commit/abc123/statuses/build/build").mock(
        return_value=Response(200, json={"key": "build", "state": "SUCCESSFUL"}),
    )
    # Act
    result = _repository(client).commit_statuses.get("abc123", "build")
    # Assert
    assert result.state == "SUCCESSFUL"


@respx.mock
def test_commit_status_update_puts_new_state(client: BitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/commit/abc123/statuses/build/build").mock(
        return_value=Response(200, json={"key": "build", "state": "SUCCESSFUL"}),
    )
    # Act
    result = _repository(client).commit_statuses.update("abc123", "build", CommitStatusUpdate(state="SUCCESSFUL"))
    # Assert
    assert result.state == "SUCCESSFUL"
    assert route.calls[0].request.content == b'{"state":"SUCCESSFUL"}'
