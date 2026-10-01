from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket.resources.branching_model import BranchingModelResource
from bitbucket.resources.default_reviewers import ProjectDefaultReviewersResource
from bitbucket.resources.deploy_keys import ProjectDeployKeysResource
from bitbucket.resources.permissions import ProjectPermissionsResource

if TYPE_CHECKING:
    from bitbucket._transport import Transport
    from bitbucket.ids import ProjectKey
    from bitbucket.ids import WorkspaceSlug


class ProjectClient:
    # A thin wiring class like RepositoryClient.
    def __init__(self, transport: Transport, workspace: WorkspaceSlug, key: ProjectKey) -> None:
        self.key = key
        self.branching_model = BranchingModelResource(transport, f"/workspaces/{workspace}/projects/{key}")
        self.default_reviewers = ProjectDefaultReviewersResource(transport, workspace, key)
        self.permissions = ProjectPermissionsResource(transport, f"/workspaces/{workspace}/projects/{key}")
        self.deploy_keys = ProjectDeployKeysResource(transport, f"/workspaces/{workspace}/projects/{key}")
