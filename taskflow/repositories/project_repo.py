"""Project repository."""

from __future__ import annotations

from typing import List

from ..models.project import Project
from .base_repo import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Persistence for Project entities."""

    table = "projects"
    model = Project

    def list_by_owner(self, owner_id: int) -> List[Project]:
        """Return all projects owned by a user."""
        return [p for p in self.list() if p.owner_id == owner_id]
