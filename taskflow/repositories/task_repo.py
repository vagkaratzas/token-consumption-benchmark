"""Task repository."""

from __future__ import annotations

from typing import List

from ..models.task import Task
from .base_repo import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Persistence for Task entities."""

    table = "tasks"
    model = Task

    def list_by_project(self, project_id: int) -> List[Task]:
        """Return all tasks belonging to a project."""
        return [t for t in self.list() if t.project_id == project_id]

    def list_by_assignee(self, assignee_id: int) -> List[Task]:
        """Return all tasks assigned to a user."""
        return [t for t in self.list() if t.assignee_id == assignee_id]
