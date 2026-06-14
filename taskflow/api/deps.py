"""Dependency wiring: builds the service graph over a single Database."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..config import Settings, load_settings
from ..db import Database
from ..repositories.project_repo import ProjectRepository
from ..repositories.task_repo import TaskRepository
from ..repositories.user_repo import UserRepository
from ..services.auth_service import AuthService
from ..services.notification_service import NotificationService
from ..services.project_service import ProjectService
from ..services.task_service import TaskService


@dataclass
class Services:
    """Container holding the wired service instances."""

    auth: AuthService
    tasks: TaskService
    projects: ProjectService
    notifications: NotificationService


def build_services(
    settings: Optional[Settings] = None, db: Optional[Database] = None
) -> Services:
    """Construct repositories and services sharing one Database."""
    settings = settings or load_settings()
    db = db or Database()
    users = UserRepository(db)
    task_repo = TaskRepository(db)
    project_repo = ProjectRepository(db)
    notifications = NotificationService()
    return Services(
        auth=AuthService(users, settings.secret_key),
        tasks=TaskService(task_repo, notifications),
        projects=ProjectService(project_repo),
        notifications=notifications,
    )
