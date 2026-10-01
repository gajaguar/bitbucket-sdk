from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket.resources.branching_model import BranchingModelResource

if TYPE_CHECKING:
    from bitbucket._transport import Transport
    from bitbucket.ids import ProjectKey
    from bitbucket.ids import WorkspaceSlug


class ProjectClient:
    # A thin wiring class like RepositoryClient; grows as Phase 3's `Projects`
    # group lands (default reviewers, permissions-config).
    def __init__(self, transport: Transport, workspace: WorkspaceSlug, key: ProjectKey) -> None:
        self.key = key
        self.branching_model = BranchingModelResource(transport, f"/workspaces/{workspace}/projects/{key}")
