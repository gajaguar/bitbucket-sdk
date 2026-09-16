from __future__ import annotations

from os import environ
from typing import Final

import pytest

from bitbucket import BitbucketClient

_LIVE_ENV_VARS: Final = ("ATLASSIAN_USER_EMAIL", "ATLASSIAN_API_KEY", "BITBUCKET_WORKSPACE")


@pytest.mark.live
@pytest.mark.skipif(
    not all(environ.get(name) for name in _LIVE_ENV_VARS),
    reason="ATLASSIAN_USER_EMAIL / ATLASSIAN_API_KEY / BITBUCKET_WORKSPACE not set",
)
def test_list_repositories_and_fetch_a_pull_request_smoke() -> None:  # pylint: disable=app-test-partial-assertion
    # Arrange
    with BitbucketClient() as client:
        workspace = client.default_workspace()
        # Act
        repositories = list(workspace.repositories.list_page(pagelen=1).items)
        # Assert
        assert repositories
        repository = workspace.repository(repositories[0].name)
        open_prs = list(repository.pull_requests.list_page(state="OPEN", pagelen=1).items)
        if open_prs:
            first_open_pr = open_prs[0]
            pull_request = repository.pull_requests.get(first_open_pr.id)
            assert pull_request.id == first_open_pr.id
