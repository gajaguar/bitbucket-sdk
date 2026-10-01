from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket.resources.branch_restrictions import BranchRestrictionsResource
from bitbucket.resources.branching_model import RepositoryBranchingModelResource
from bitbucket.resources.commit_statuses import CommitStatusesResource
from bitbucket.resources.commits import CommitsResource
from bitbucket.resources.default_reviewers import DefaultReviewersResource
from bitbucket.resources.deploy_keys import DeployKeysResource
from bitbucket.resources.deployments import DeploymentsResource
from bitbucket.resources.downloads import DownloadsResource
from bitbucket.resources.environments import EnvironmentsResource
from bitbucket.resources.hooks import HooksResource
from bitbucket.resources.permissions import RepositoryPermissionsResource
from bitbucket.resources.pipelines import PipelinesResource
from bitbucket.resources.pipelines_config import RepositoryPipelinesConfig
from bitbucket.resources.pull_requests import PullRequestsResource
from bitbucket.resources.refs import RefsResource
from bitbucket.resources.source import SourceResource

if TYPE_CHECKING:
    from bitbucket._transport import Transport
    from bitbucket.ids import RepositorySlug
    from bitbucket.ids import WorkspaceSlug


class RepositoryClient:  # pylint: disable=too-many-instance-attributes
    # Grows by one attribute per resource group Roadmap Phase 2 adds; a thin
    # wiring class, not a design smell — see docs/architecture/layering.md.
    def __init__(self, transport: Transport, workspace: WorkspaceSlug, slug: RepositorySlug) -> None:
        self.slug = slug
        base_path = f"/repositories/{workspace}/{slug}"
        self.pull_requests = PullRequestsResource(transport, workspace, slug)
        self.default_reviewers = DefaultReviewersResource(transport, workspace, slug)
        self.commit_statuses = CommitStatusesResource(transport, workspace, slug)
        self.hooks = HooksResource(transport, base_path)
        self.permissions = RepositoryPermissionsResource(transport, base_path)
        self.refs = RefsResource(transport, base_path)
        self.source = SourceResource(transport, base_path)
        self.commits = CommitsResource(transport, base_path)
        self.downloads = DownloadsResource(transport, base_path)
        self.branch_restrictions = BranchRestrictionsResource(transport, base_path)
        self.branching_model = RepositoryBranchingModelResource(transport, base_path)
        self.pipelines = PipelinesResource(transport, base_path)
        self.pipelines_config = RepositoryPipelinesConfig(transport, base_path)
        self.environments = EnvironmentsResource(transport, base_path)
        self.deployments = DeploymentsResource(transport, base_path)
        self.deploy_keys = DeployKeysResource(transport, base_path)
