from __future__ import annotations

from bitbucket.aio.resources.base import AsyncDeletableResourceMixin
from bitbucket.aio.resources.base import AsyncNestedResource
from bitbucket.models.project import Project
from bitbucket.models.project import ProjectCreate
from bitbucket.models.project import ProjectUpdate


# Async mirror of resources.projects.ProjectsResource.
class AsyncProjectsResource(AsyncNestedResource[Project, ProjectCreate, ProjectUpdate], AsyncDeletableResourceMixin):
    _path = "/projects"
    _read_model = Project
