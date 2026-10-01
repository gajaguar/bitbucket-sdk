from __future__ import annotations

from bitbucket.aio.resources.base import AsyncDeletableResourceMixin
from bitbucket.aio.resources.base import AsyncNestedResource
from bitbucket.models.branch_restriction import BranchRestriction
from bitbucket.models.branch_restriction import BranchRestrictionCreate
from bitbucket.models.branch_restriction import BranchRestrictionUpdate


class AsyncBranchRestrictionsResource(
    AsyncNestedResource[BranchRestriction, BranchRestrictionCreate, BranchRestrictionUpdate],
    AsyncDeletableResourceMixin,
):
    _path = "/branch-restrictions"
    _read_model = BranchRestriction
