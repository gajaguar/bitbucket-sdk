from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket.aio.resources.branching_model import AsyncBranchingModelResource
from bitbucket.aio.resources.default_reviewers import AsyncProjectDefaultReviewersResource
from bitbucket.aio.resources.deploy_keys import AsyncProjectDeployKeysResource
from bitbucket.aio.resources.permissions import AsyncProjectPermissionsResource

if TYPE_CHECKING:
    from bitbucket.aio._transport import AsyncTransport
    from bitbucket.ids import ProjectKey
    from bitbucket.ids import WorkspaceSlug


class AsyncProjectClient:
    # Async mirror of ProjectClient.
    def __init__(self, transport: AsyncTransport, workspace: WorkspaceSlug, key: ProjectKey) -> None:
        self.key = key
        self.branching_model = AsyncBranchingModelResource(transport, f"/workspaces/{workspace}/projects/{key}")
        self.default_reviewers = AsyncProjectDefaultReviewersResource(transport, workspace, key)
        self.permissions = AsyncProjectPermissionsResource(transport, f"/workspaces/{workspace}/projects/{key}")
        self.deploy_keys = AsyncProjectDeployKeysResource(transport, f"/workspaces/{workspace}/projects/{key}")
