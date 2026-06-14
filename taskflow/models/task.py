"""Task domain model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .base import BaseModel


class Status(str, Enum):
    """Lifecycle states for a task."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@dataclass
class Task(BaseModel):
    """A unit of work that belongs to a project and may be assigned to a user."""

    title: str = ""
    description: str = ""
    status: Status = Status.TODO
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None

    def is_open(self) -> bool:
        """Return True if the task is not yet done."""
        return self.status != Status.DONE
