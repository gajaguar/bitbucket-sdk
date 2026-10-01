from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket.aio.resources.branch_restrictions import AsyncBranchRestrictionsResource
from bitbucket.aio.resources.branching_model import AsyncRepositoryBranchingModelResource
from bitbucket.aio.resources.commit_statuses import AsyncCommitStatusesResource
from bitbucket.aio.resources.commits import AsyncCommitsResource
from bitbucket.aio.resources.default_reviewers import AsyncDefaultReviewersResource
from bitbucket.aio.resources.deploy_keys import AsyncDeployKeysResource
from bitbucket.aio.resources.deployments import AsyncDeploymentsResource
from bitbucket.aio.resources.downloads import AsyncDownloadsResource
from bitbucket.aio.resources.environments import AsyncEnvironmentsResource
from bitbucket.aio.resources.hooks import AsyncHooksResource
from bitbucket.aio.resources.permissions import AsyncRepositoryPermissionsResource
from bitbucket.aio.resources.pipelines import AsyncPipelinesResource
from bitbucket.aio.resources.pipelines_config import AsyncRepositoryPipelinesConfig
from bitbucket.aio.resources.properties import AsyncPropertiesResource
from bitbucket.aio.resources.pull_requests import AsyncPullRequestsResource
from bitbucket.aio.resources.refs import AsyncRefsResource
from bitbucket.aio.resources.source import AsyncSourceResource

if TYPE_CHECKING:
    from bitbucket.aio._transport import AsyncTransport
    from bitbucket.ids import RepositorySlug
    from bitbucket.ids import WorkspaceSlug


class AsyncRepositoryClient:  # pylint: disable=too-many-instance-attributes
    # Async mirror of RepositoryClient — see that class's comment; grows by one
    # attribute per resource group Roadmap Phase 2 adds.
    def __init__(self, transport: AsyncTransport, workspace: WorkspaceSlug, slug: RepositorySlug) -> None:
        self.slug = slug
        base_path = f"/repositories/{workspace}/{slug}"
        self.pull_requests = AsyncPullRequestsResource(transport, workspace, slug)
        self.default_reviewers = AsyncDefaultReviewersResource(transport, workspace, slug)
        self.commit_statuses = AsyncCommitStatusesResource(transport, workspace, slug)
        self.hooks = AsyncHooksResource(transport, base_path)
        self.permissions = AsyncRepositoryPermissionsResource(transport, base_path)
        self.refs = AsyncRefsResource(transport, base_path)
        self.source = AsyncSourceResource(transport, base_path)
        self.commits = AsyncCommitsResource(transport, base_path)
        self.downloads = AsyncDownloadsResource(transport, base_path)
        self.branch_restrictions = AsyncBranchRestrictionsResource(transport, base_path)
        self.branching_model = AsyncRepositoryBranchingModelResource(transport, base_path)
        self.pipelines = AsyncPipelinesResource(transport, base_path)
        self.pipelines_config = AsyncRepositoryPipelinesConfig(transport, base_path)
        self.environments = AsyncEnvironmentsResource(transport, base_path)
        self.deployments = AsyncDeploymentsResource(transport, base_path)
        self.deploy_keys = AsyncDeployKeysResource(transport, base_path)
        self.properties = AsyncPropertiesResource(transport, base_path)
