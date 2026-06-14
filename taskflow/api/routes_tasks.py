"""Task HTTP routes (api -> TaskService -> TaskRepository -> Database)."""

from __future__ import annotations

from .app import App


def register(app: App) -> None:
    """Register task routes on the app."""

    def create_task(app: App, body: dict) -> dict:
        task = app.services.tasks.create_task(
            title=body.get("title", ""),
            project_id=body.get("project_id"),
            assignee_id=body.get("assignee_id"),
        )
        return {"status": 201, "task": task.to_dict()}

    def complete_task(app: App, body: dict) -> dict:
        task = app.services.tasks.complete_task(body["task_id"])
        if task is None:
            return {"status": 404, "error": "task not found"}
        return {"status": 200, "task": task.to_dict()}

    app.register("POST", "/tasks", create_task)
    app.register("POST", "/tasks/complete", complete_task)
