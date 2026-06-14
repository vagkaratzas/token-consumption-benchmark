"""Task lifecycle business logic."""

from __future__ import annotations

from typing import List, Optional

from ..models.task import Status, Task
from ..repositories.task_repo import TaskRepository
from .notification_service import NotificationService


class TaskService:
    """Creates and transitions tasks, notifying assignees of changes."""

    def __init__(
        self, tasks: TaskRepository, notifications: NotificationService
    ) -> None:
        self.tasks = tasks
        self.notifications = notifications

    def create_task(
        self, title: str, project_id: int, assignee_id: Optional[int] = None
    ) -> Task:
        """Create a new task in a project and notify the assignee."""
        # TODO: validate that project_id refers to an existing project.
        task = Task(title=title, project_id=project_id, assignee_id=assignee_id)
        task = self.tasks.add(task)
        if assignee_id is not None:
            self.notifications.notify(
                assignee_id, f"Assigned task #{task.id}: {title}"
            )
        return task

    def assign_task(self, task_id: int, assignee_id: int) -> Optional[Task]:
        """Assign an existing task to a user."""
        task = self.tasks.update(task_id, {"assignee_id": assignee_id})
        if task is not None:
            self.notifications.notify(assignee_id, f"Assigned task #{task_id}")
        return task

    def complete_task(self, task_id: int) -> Optional[Task]:
        """Mark a task as done and notify its assignee."""
        # FIXME: should reject completion if the task is already DONE.
        task = self.tasks.update(task_id, {"status": Status.DONE})
        if task is not None and task.assignee_id is not None:
            self.notifications.notify(task.assignee_id, f"Task #{task_id} completed")
        return task

    def open_tasks(self, project_id: int) -> List[Task]:
        """Return the open (not done) tasks for a project."""
        return [t for t in self.tasks.list_by_project(project_id) if t.is_open()]
