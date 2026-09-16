from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket.resources.default_reviewers import DefaultReviewersResource
from bitbucket.resources.pull_requests import PullRequestsResource

if TYPE_CHECKING:
    from bitbucket._transport import Transport
    from bitbucket.ids import RepositorySlug
    from bitbucket.ids import WorkspaceSlug


class RepositoryClient:
    def __init__(self, transport: Transport, workspace: WorkspaceSlug, slug: RepositorySlug) -> None:
        self.slug = slug
        self.pull_requests = PullRequestsResource(transport, workspace, slug)
        self.default_reviewers = DefaultReviewersResource(transport, workspace, slug)
