from __future__ import annotations

from bitbucket.models.comment import CommentCreate
from bitbucket.models.comment import CommentUpdate
from bitbucket.models.comment import PullRequestComment
from bitbucket.resources.base import DeletableResourceMixin
from bitbucket.resources.base import NestedResource


class CommentsResource(NestedResource[PullRequestComment, CommentCreate, CommentUpdate], DeletableResourceMixin):
    _path = "/comments"
    _read_model = PullRequestComment
