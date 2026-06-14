"""Project HTTP routes (api -> ProjectService -> ProjectRepository -> Database)."""

from __future__ import annotations

from .app import App


def register(app: App) -> None:
    """Register project routes on the app."""

    def create_project(app: App, body: dict) -> dict:
        project = app.services.projects.create_project(
            name=body.get("name", ""), owner_id=body.get("owner_id")
        )
        return {"status": 201, "project": project.to_dict()}

    def add_member(app: App, body: dict) -> dict:
        project = app.services.projects.add_member(
            body["project_id"], body["user_id"]
        )
        if project is None:
            return {"status": 404, "error": "project not found"}
        return {"status": 200, "project": project.to_dict()}

    app.register("POST", "/projects", create_project)
    app.register("POST", "/projects/members", add_member)
