from __future__ import annotations

from bitbucket.models.project import Project
from bitbucket.models.project import ProjectCreate
from bitbucket.models.project import ProjectUpdate
from bitbucket.resources.base import DeletableResourceMixin
from bitbucket.resources.base import NestedResource


# POST/PUT/DELETE answer the project itself, so the generic CRUD shape fits.
# `PUT {path}/{key}` creates or updates; `POST {path}` creates only.
class ProjectsResource(NestedResource[Project, ProjectCreate, ProjectUpdate], DeletableResourceMixin):
    _path = "/projects"
    _read_model = Project
