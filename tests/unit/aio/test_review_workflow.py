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
from bitbucket.models.conflict import FileConflictScenario
from bitbucket.models.mergeability import GitMergeabilityReason
from bitbucket.models.mergeability import MergeabilityCheckStatus
from bitbucket.models.mergeability import MergeabilityCheckType
from bitbucket.models.mergeability import MergeabilityPullRequestState
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
    from bitbucket.aio.client import AsyncBitbucketClient


def _pull_requests(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").repository("repo").pull_requests


def _comments(aclient: AsyncBitbucketClient):
    return _pull_requests(aclient).comments(5)


def _tasks(aclient: AsyncBitbucketClient):
    return _pull_requests(aclient).tasks(5)


def _repository(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").repository("repo")


@respx.mock
async def test_pull_request_list_filters_by_state_and_query(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(
        return_value=Response(200, json={"values": [{"id": 1, "title": "Fix bug", "state": "OPEN"}], "next": None}),
    )
    # Act
    pull_requests = [item async for item in _pull_requests(aclient).list(state="OPEN", q='title~"fix"')]
    # Assert
    assert [pr.id for pr in pull_requests] == [1]
    assert dict(route.calls[0].request.url.params) == {"state": "OPEN", "q": 'title~"fix"'}


# respx matches routes in registration order, so the page-2 route (filtered on
# params) must be registered first — otherwise the unfiltered first-page route
# would also catch the page-2 request and loop forever.
@respx.mock
async def test_pull_request_list_follows_next_cursor_across_pages(aclient: AsyncBitbucketClient) -> None:
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
    pull_requests = [item async for item in _pull_requests(aclient).list()]
    # Assert
    assert [pr.id for pr in pull_requests] == [1, 2]


@respx.mock
async def test_pull_request_get_returns_pull_request(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/42").mock(
        return_value=Response(200, json={"id": 42, "title": "Fix bug"}),
    )
    # Act
    pull_request = await _pull_requests(aclient).get(42)
    # Assert
    assert pull_request.id == 42
    assert pull_request.title == "Fix bug"


@respx.mock
async def test_pull_request_get_raises_not_found_for_unknown_id(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/42").mock(
        return_value=Response(404, json={"error": {"message": "nope"}}),
    )
    # Act
    with pytest.raises(NotFoundError) as exc_info:
        await _pull_requests(aclient).get(42)
    # Assert
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "nope"


@respx.mock
async def test_pull_request_get_raises_transport_error_for_invalid_json_body(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/42").mock(
        return_value=Response(200, content=b"not json", headers={"content-type": "application/json"}),
    )
    # Act
    # Assert
    with pytest.raises(TransportError, match="Invalid JSON"):
        await _pull_requests(aclient).get(42)


@respx.mock
async def test_pull_request_diff_returns_raw_text(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/diff").mock(
        return_value=Response(200, text="diff --git a b"),
    )
    # Act
    diff = await _pull_requests(aclient).diff(5)
    # Assert
    assert diff == "diff --git a b"


@respx.mock
async def test_pull_request_diff_raises_not_found_for_unknown_id(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/diff").mock(
        return_value=Response(404, json={"error": {"message": "nope"}}),
    )
    # Act
    with pytest.raises(NotFoundError) as exc_info:
        await _pull_requests(aclient).diff(5)
    # Assert
    assert exc_info.value.status_code == 404


@respx.mock
async def test_pull_request_statuses_list_returns_build_statuses(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/statuses").mock(
        return_value=Response(200, json={"values": [{"key": "build", "state": "SUCCESSFUL"}], "next": None}),
    )
    # Act
    statuses = [item async for item in _pull_requests(aclient).statuses(5).list()]
    # Assert
    assert [status.key for status in statuses] == ["build"]
    assert [status.state for status in statuses] == ["SUCCESSFUL"]


@respx.mock
async def test_pull_request_comment_create_posts_content_payload(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments").mock(
        return_value=Response(200, json={"id": 99}),
    )
    payload = CommentCreate(content=CommentContentCreate(raw="nice"))
    # Act
    result = await _comments(aclient).create(payload)
    # Assert
    assert result.id == 99
    assert route.calls[0].request.content == b'{"content":{"raw":"nice"}}'


@respx.mock
async def test_pull_request_comment_list_sorts_by_created_on(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments").mock(
        return_value=Response(200, json={"values": [{"id": 1}], "next": None}),
    )
    # Act
    comments = [item async for item in _comments(aclient).list(sort="-created_on")]
    # Assert
    assert [comment.id for comment in comments] == [1]
    assert dict(route.calls[0].request.url.params) == {"sort": "-created_on"}


@respx.mock
async def test_pull_request_comment_get_returns_comment(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments/9").mock(
        return_value=Response(200, json={"id": 9}),
    )
    # Act
    comment = await _comments(aclient).get(9)
    # Assert
    assert comment.id == 9


@respx.mock
async def test_pull_request_comment_update_puts_edited_content(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments/9").mock(
        return_value=Response(200, json={"id": 9}),
    )
    # Act
    result = await _comments(aclient).update(9, CommentUpdate(content=CommentContentCreate(raw="edited")))
    # Assert
    assert result.id == 9
    assert route.calls[0].request.content == b'{"content":{"raw":"edited"}}'


@respx.mock
async def test_pull_request_comment_delete_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments/9").mock(
        return_value=Response(204),
    )
    # Act
    result = await _comments(aclient).delete(9)
    # Assert
    assert result is None
    assert route.called


@respx.mock
async def test_pull_request_approve_returns_approving_account(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/approve").mock(
        return_value=Response(200, json={"uuid": "{abc}"}),
    )
    # Act
    result = await _pull_requests(aclient).approve(5)
    # Assert
    assert result.uuid == "{abc}"
    assert route.calls[0].request.content == b""


@respx.mock
async def test_pull_request_approve_raises_server_error_on_upstream_failure(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/approve").mock(
        return_value=Response(500, text="boom"),
    )
    # Act
    with pytest.raises(ServerError) as exc_info:
        await _pull_requests(aclient).approve(5)
    # Assert
    assert exc_info.value.status_code == 500
    assert exc_info.value.raw == "boom"


@respx.mock
async def test_pull_request_create_posts_title_and_source_branch(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests").mock(
        return_value=Response(200, json={"id": 7, "title": "New PR"}),
    )
    payload = PullRequestCreate(title="New PR", source=EndpointSpec(branch=BranchSpec(name="feature")))
    # Act
    result = await _pull_requests(aclient).create(payload)
    # Assert
    assert result.id == 7
    assert route.calls[0].request.content == b'{"title":"New PR","source":{"branch":{"name":"feature"}}}'


@respx.mock
async def test_pull_request_update_puts_only_the_changed_title(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/pullrequests/5").mock(
        return_value=Response(200, json={"id": 5, "title": "Renamed"}),
    )
    # Act
    result = await _pull_requests(aclient).update(5, PullRequestUpdate(title="Renamed"))
    # Assert
    assert result.title == "Renamed"
    assert route.calls[0].request.content == b'{"title":"Renamed"}'


@respx.mock
async def test_pull_request_commits_returns_commit_hashes(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/commits").mock(
        return_value=Response(200, json={"values": [{"hash": "abc123"}], "next": None}),
    )
    # Act
    commits = [item async for item in _pull_requests(aclient).commits(5)]
    # Assert
    assert [commit.hash for commit in commits] == ["abc123"]


@respx.mock
async def test_pull_request_conflicts_returns_conflicting_files(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/conflicts").mock(
        return_value=Response(200, json={"values": [{"path": "a.py"}], "next": None}),
    )
    # Act
    conflicts = [item async for item in _pull_requests(aclient).conflicts(5)]
    # Assert
    assert [conflict.path for conflict in conflicts] == ["a.py"]


@respx.mock
async def test_pull_request_diffstat_returns_line_counts(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/diffstat").mock(
        return_value=Response(200, json={"values": [{"lines_added": 3, "lines_removed": 1}], "next": None}),
    )
    # Act
    stats = [item async for item in _pull_requests(aclient).diffstat(5)]
    # Assert
    assert [stat.lines_added for stat in stats] == [3]


@respx.mock
async def test_pull_request_mbox_format_export_returns_raw_text(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/patch").mock(
        return_value=Response(200, text="From abc123"),
    )
    # Act
    result = await _pull_requests(aclient).patch(5)
    # Assert
    assert result == "From abc123"


@respx.mock
async def test_pull_request_activity_returns_activity_feed(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/activity").mock(
        return_value=Response(200, json={"values": [{"update": {"state": "OPEN"}}], "next": None}),
    )
    # Act
    activity = [item async for item in _pull_requests(aclient).activity(5)]
    # Assert
    assert [entry.update.state for entry in activity] == ["OPEN"]


@respx.mock
async def test_repository_pull_request_activity_returns_repo_wide_feed(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/activity").mock(
        return_value=Response(200, json={"values": [{"update": {"state": "MERGED"}}], "next": None}),
    )
    # Act
    activity = [item async for item in aclient.workspace("ws").repositories.pull_request_activity("repo")]
    # Assert
    assert [entry.update.state for entry in activity] == ["MERGED"]


@respx.mock
async def test_repository_commit_pull_requests_returns_prs_containing_commit(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/commit/abc123/pullrequests").mock(
        return_value=Response(200, json={"values": [{"id": 9}], "next": None}),
    )
    # Act
    pull_requests = [
        item async for item in aclient.workspace("ws").repositories.commit_pull_requests("repo", "abc123")
    ]
    # Assert
    assert [pr.id for pr in pull_requests] == [9]


@respx.mock
async def test_pull_request_task_create_posts_content_payload(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/tasks").mock(
        return_value=Response(200, json={"id": 1}),
    )
    payload = TaskCreate(content=TaskContentCreate(raw="fix this"))
    # Act
    result = await _tasks(aclient).create(payload)
    # Assert
    assert result.id == 1
    assert route.calls[0].request.content == b'{"content":{"raw":"fix this"}}'


@respx.mock
async def test_pull_request_task_list_returns_tasks(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/tasks").mock(
        return_value=Response(200, json={"values": [{"id": 1, "state": "UNRESOLVED"}], "next": None}),
    )
    # Act
    tasks = [item async for item in _tasks(aclient).list()]
    # Assert
    assert [task.state for task in tasks] == ["UNRESOLVED"]


@respx.mock
async def test_pull_request_task_update_puts_resolved_state(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/tasks/1").mock(
        return_value=Response(200, json={"id": 1, "state": "RESOLVED"}),
    )
    # Act
    result = await _tasks(aclient).update(1, TaskUpdate(state="RESOLVED"))
    # Assert
    assert result.state == "RESOLVED"
    assert route.calls[0].request.content == b'{"state":"RESOLVED"}'


@respx.mock
async def test_pull_request_task_delete_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/tasks/1").mock(
        return_value=Response(204),
    )
    # Act
    result = await _tasks(aclient).delete(1)
    # Assert
    assert result is None
    assert route.called


@respx.mock
async def test_pull_request_comment_resolve_returns_resolved_comment(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments/9/resolve").mock(
        return_value=Response(200, json={"id": 9, "pending": False}),
    )
    # Act
    result = await _comments(aclient).resolve(9)
    # Assert
    assert result.id == 9
    assert route.calls[0].request.content == b""


@respx.mock
async def test_pull_request_comment_unresolve_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/comments/9/resolve").mock(
        return_value=Response(204),
    )
    # Act
    result = await _comments(aclient).unresolve(9)
    # Assert
    assert result is None
    assert route.called


@respx.mock
async def test_pull_request_properties_get_returns_stored_value(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/properties/my-app/state").mock(
        return_value=Response(200, json={"stage": "review"}),
    )
    # Act
    value = await _pull_requests(aclient).properties(5).get("my-app", "state")
    # Assert
    assert value == {"stage": "review"}


@respx.mock
async def test_pull_request_properties_put_sends_value_as_body(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/properties/my-app/state").mock(
        return_value=Response(204),
    )
    # Act
    result = await _pull_requests(aclient).properties(5).put("my-app", "state", {"stage": "done"})
    # Assert
    assert result is None
    assert route.calls[0].request.content == b'{"stage":"done"}'


@respx.mock
async def test_pull_request_properties_delete_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/properties/my-app/state").mock(
        return_value=Response(204),
    )
    # Act
    result = await _pull_requests(aclient).properties(5).delete("my-app", "state")
    # Assert
    assert result is None
    assert route.called


@respx.mock
async def test_default_reviewer_get_returns_reviewer(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/default-reviewers/alice").mock(
        return_value=Response(200, json={"uuid": "{x}"}),
    )
    # Act
    reviewer = await _repository(aclient).default_reviewers.get("alice")
    # Assert
    assert reviewer.uuid == "{x}"


@respx.mock
async def test_default_reviewer_add_puts_target_username(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/default-reviewers/alice").mock(
        return_value=Response(200, json={"uuid": "{x}"}),
    )
    # Act
    reviewer = await _repository(aclient).default_reviewers.add("alice")
    # Assert
    assert reviewer.uuid == "{x}"
    assert route.called


@respx.mock
async def test_default_reviewer_remove_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/default-reviewers/alice").mock(
        return_value=Response(204),
    )
    # Act
    result = await _repository(aclient).default_reviewers.remove("alice")
    # Assert
    assert result is None
    assert route.called


@respx.mock
async def test_default_reviewer_effective_returns_repo_and_project_reviewers(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/effective-default-reviewers").mock(
        return_value=Response(200, json={"values": [{"uuid": "{x}", "reviewer_type": "project"}], "next": None}),
    )
    # Act
    reviewers = [item async for item in _repository(aclient).default_reviewers.effective()]
    # Assert
    assert [reviewer.reviewer_type for reviewer in reviewers] == ["project"]


@respx.mock
async def test_commit_status_list_returns_build_statuses(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/commit/abc123/statuses").mock(
        return_value=Response(200, json={"values": [{"key": "build"}], "next": None}),
    )
    # Act
    statuses = [item async for item in _repository(aclient).commit_statuses.list("abc123")]
    # Assert
    assert [status.key for status in statuses] == ["build"]


@respx.mock
async def test_commit_status_create_posts_build_status(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/commit/abc123/statuses/build").mock(
        return_value=Response(200, json={"key": "build", "state": "INPROGRESS"}),
    )
    payload = CommitStatusCreate(key="build", state="INPROGRESS", url="https://ci.example.com/1")
    # Act
    result = await _repository(aclient).commit_statuses.create("abc123", payload)
    # Assert
    assert result.state == "INPROGRESS"
    assert route.calls[0].request.content == (b'{"key":"build","state":"INPROGRESS","url":"https://ci.example.com/1"}')


@respx.mock
async def test_commit_status_get_returns_build_status(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/commit/abc123/statuses/build/build").mock(
        return_value=Response(200, json={"key": "build", "state": "SUCCESSFUL"}),
    )
    # Act
    result = await _repository(aclient).commit_statuses.get("abc123", "build")
    # Assert
    assert result.state == "SUCCESSFUL"


@respx.mock
async def test_commit_status_update_puts_new_state(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/repositories/ws/repo/commit/abc123/statuses/build/build").mock(
        return_value=Response(200, json={"key": "build", "state": "SUCCESSFUL"}),
    )
    # Act
    result = await _repository(aclient).commit_statuses.update(
        "abc123", "build", CommitStatusUpdate(state="SUCCESSFUL")
    )
    # Assert
    assert result.state == "SUCCESSFUL"
    assert route.calls[0].request.content == b'{"state":"SUCCESSFUL"}'


@respx.mock
async def test_pull_request_conflicts_parse_scenario_and_message(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/conflicts").mock(
        return_value=Response(
            200,
            json={
                "values": [{"path": "a.py", "scenario": "content", "message": "both"}, {"scenario": "new"}],
                "next": None,
            },
        ),
    )
    # Act
    conflicts = [item async for item in _pull_requests(aclient).conflicts(5)]
    # Assert
    assert [conflict.scenario for conflict in conflicts] == [
        FileConflictScenario.CONTENT,
        FileConflictScenario.UNKNOWN,
    ]
    assert conflicts[0].message == "both"


@respx.mock
async def test_pull_request_mergeability_checks_returns_parsed_checks(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/mergeability/checks").mock(
        return_value=Response(
            200,
            json={
                "size": 4,
                "values": [
                    {
                        "type": "pullrequest_state_check",
                        "status": "PASSED",
                        "required": True,
                        "blocking": False,
                        "state": "OPEN",
                    },
                    {
                        "type": "git_mergeability_check",
                        "status": "FAILED",
                        "required": True,
                        "blocking": True,
                        "reason": "conflicts",
                        "links": {"details": {"href": "https://x/conflicts"}},
                    },
                    {
                        "type": "merge_queue_check",
                        "status": "PASSED",
                        "queued": False,
                        "merge_queue": {"uuid": "{q}", "name": "main", "state": "ACTIVE"},
                    },
                    {"type": "brand_new_check", "status": "WEIRD", "check": {"kind": "minimum_approvals"}},
                ],
            },
        ),
    )
    # Act
    checks = await _pull_requests(aclient).mergeability_checks(5)
    # Assert
    assert [check.type for check in checks][:3] == [
        MergeabilityCheckType.PULLREQUEST_STATE_CHECK,
        MergeabilityCheckType.GIT_MERGEABILITY_CHECK,
        MergeabilityCheckType.MERGE_QUEUE_CHECK,
    ]
    assert checks[0].state is MergeabilityPullRequestState.OPEN
    assert checks[1].reason is GitMergeabilityReason.CONFLICTS
    assert checks[1].blocking is True
    assert checks[1].links is not None
    assert checks[1].links.details is not None
    assert checks[1].links.details.href == "https://x/conflicts"
    assert checks[2].merge_queue is not None
    assert checks[2].merge_queue.state == "ACTIVE"
    assert checks[3].type is MergeabilityCheckType.UNKNOWN
    assert checks[3].status is MergeabilityCheckStatus.UNKNOWN
    assert checks[3].check is not None
    assert checks[3].check.kind == "minimum_approvals"
    assert route.calls[0].request.url.query == b""


@respx.mock
async def test_pull_request_mergeability_checks_sends_q_filter(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/mergeability/checks").mock(
        return_value=Response(200, json={"values": []}),
    )
    # Act
    checks = await _pull_requests(aclient).mergeability_checks(5, q='type!="git_mergeability_check"')
    # Assert
    assert checks == []
    assert route.calls[0].request.url.params["q"] == 'type!="git_mergeability_check"'
