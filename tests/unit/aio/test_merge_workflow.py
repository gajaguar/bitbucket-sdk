from __future__ import annotations

from typing import TYPE_CHECKING

import respx
from httpx import Response

from bitbucket.models.merge import MergeParameters
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.aio.client import AsyncBitbucketClient


def _pull_requests(aclient: AsyncBitbucketClient):
    return aclient.workspace("ws").repository("repo").pull_requests


@respx.mock
async def test_pull_request_merge_posts_strategy_and_returns_task(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/merge").mock(
        return_value=Response(202, json={"task_id": "abc"}),
    )
    payload = MergeParameters(merge_strategy="squash")
    # Act
    task = await _pull_requests(aclient).merge(5, payload)
    # Assert
    assert task.task_id == "abc"
    assert route.calls[0].request.content == b'{"merge_strategy":"squash"}'


@respx.mock
async def test_pull_request_merge_task_status_returns_terminal_state(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/merge/task-status/abc").mock(
        return_value=Response(200, json={"task_status": "SUCCESS"}),
    )
    # Act
    status = await _pull_requests(aclient).merge_task_status(5, "abc")
    # Assert
    assert status.task_status == "SUCCESS"


@respx.mock
async def test_pull_request_merge_and_wait_polls_until_terminal(aclient: AsyncBitbucketClient) -> None:  # pylint: disable=gajaguar-test-no-blank-lines
    # fmt: off
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
    async def _collect_sleep(delay: float) -> None:  # ruff: ignore[unused-async, blank-lines-before-nested-definition]
        delays.append(delay)
    # Act
    status = await _pull_requests(aclient).merge_and_wait(5, sleep=_collect_sleep)
    # Assert
    assert status.task_status == "SUCCESS"
    assert delays == [1.0]
    # fmt: on


@respx.mock
async def test_pull_request_unapprove_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/approve").mock(
        return_value=Response(204),
    )
    # Act
    result = await _pull_requests(aclient).unapprove(5)
    # Assert
    assert result is None
    assert route.called


@respx.mock
async def test_pull_request_decline_returns_declined_pull_request(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/decline").mock(
        return_value=Response(200, json={"id": 5, "state": "DECLINED"}),
    )
    # Act
    result = await _pull_requests(aclient).decline(5)
    # Assert
    assert result.state == "DECLINED"


@respx.mock
async def test_pull_request_request_changes_returns_participant_account(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    respx.post(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/request-changes").mock(
        return_value=Response(200, json={"uuid": "{abc}"}),
    )
    # Act
    result = await _pull_requests(aclient).request_changes(5)
    # Assert
    assert result.uuid == "{abc}"


@respx.mock
async def test_pull_request_unrequest_changes_returns_none(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.delete(f"{BASE_URL}/repositories/ws/repo/pullrequests/5/request-changes").mock(
        return_value=Response(204),
    )
    # Act
    result = await _pull_requests(aclient).unrequest_changes(5)
    # Assert
    assert result is None
    assert route.called
