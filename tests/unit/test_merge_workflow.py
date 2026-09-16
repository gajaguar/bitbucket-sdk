from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

from bitbucket.models.merge import MergeParameters
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.client import BitbucketClient


def _pull_requests(client: BitbucketClient):
    return client.workspace("ws").repository("repo").pull_requests


@respx.mock
def test_pull_request_merge_posts_strategy_and_returns_task(client: BitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/merge").mock(
        return_value=Response(202, json={"task_id": "abc"}),
    )
    payload = MergeParameters(merge_strategy="squash")
    # Act
    task = _pull_requests(client).merge(5, payload)
    # Assert
    assert task.task_id == "abc"
    assert route.calls[0].request.content == b'{"merge_strategy":"squash"}'


@respx.mock
def test_pull_request_merge_task_status_returns_terminal_state(client: BitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/merge/task-status/abc").mock(
        return_value=Response(200, json={"task_status": "SUCCESS"}),
    )
    # Act
    status = _pull_requests(client).merge_task_status(5, "abc")
    # Assert
    assert status.task_status == "SUCCESS"


@respx.mock
def test_pull_request_merge_and_wait_polls_until_terminal(client: BitbucketClient) -> None:
    # Arrange
    respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/merge").mock(
        return_value=Response(202, json={"task_id": "abc"}),
    )
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/merge/task-status/abc").mock(
        side_effect=[
            Response(200, json={"task_status": "PENDING"}),
            Response(200, json={"task_status": "SUCCESS"}),
        ],
    )
    delays: list[float] = []
    # Act
    status = _pull_requests(client).merge_and_wait(5, sleep=delays.append)
    # Assert
    assert status.task_status == "SUCCESS"
    assert delays == [1.0]


@respx.mock
def test_pull_request_unapprove_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/approve").mock(
        return_value=Response(204),
    )
    # Act
    result = _pull_requests(client).unapprove(5)
    # Assert
    assert result is None
    assert route.called


@respx.mock
def test_pull_request_decline_returns_declined_pull_request(client: BitbucketClient) -> None:
    # Arrange
    respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/decline").mock(
        return_value=Response(200, json={"id": 5, "state": "DECLINED"}),
    )
    # Act
    result = _pull_requests(client).decline(5)
    # Assert
    assert result.state == "DECLINED"


@respx.mock
def test_pull_request_request_changes_returns_participant_account(client: BitbucketClient) -> None:
    # Arrange
    respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/request-changes").mock(
        return_value=Response(200, json={"uuid": "{abc}"}),
    )
    # Act
    result = _pull_requests(client).request_changes(5)
    # Assert
    assert result.uuid == "{abc}"


@respx.mock
def test_pull_request_unrequest_changes_returns_none(client: BitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/request-changes").mock(
        return_value=Response(204),
    )
    # Act
    result = _pull_requests(client).unrequest_changes(5)
    # Assert
    assert result is None
    assert route.called
