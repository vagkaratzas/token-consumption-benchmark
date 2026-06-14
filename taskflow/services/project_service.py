"""Project management business logic."""

from __future__ import annotations

from typing import Optional

from ..models.project import Project
from ..repositories.project_repo import ProjectRepository


class ProjectService:
    """Creates projects and manages membership."""

    def __init__(self, projects: ProjectRepository) -> None:
        self.projects = projects

    def create_project(self, name: str, owner_id: int) -> Project:
        """Create a project owned by a user (owner is the first member)."""
        project = Project(name=name, owner_id=owner_id, member_ids=[owner_id])
        return self.projects.add(project)

    def add_member(self, project_id: int, user_id: int) -> Optional[Project]:
        """Add a member to a project and persist the change."""
        project = self.projects.get(project_id)
        if project is None:
            return None
        project.add_member(user_id)
        return self.projects.update(project_id, {"member_ids": project.member_ids})
