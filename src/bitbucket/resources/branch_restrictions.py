from __future__ import annotations

from bitbucket.models.branch_restriction import BranchRestriction
from bitbucket.models.branch_restriction import BranchRestrictionCreate
from bitbucket.models.branch_restriction import BranchRestrictionUpdate
from bitbucket.resources.base import DeletableResourceMixin
from bitbucket.resources.base import NestedResource


class BranchRestrictionsResource(
    NestedResource[BranchRestriction, BranchRestrictionCreate, BranchRestrictionUpdate],
    DeletableResourceMixin,
):
    _path = "/branch-restrictions"
    _read_model = BranchRestriction
