"""User HTTP routes (api -> AuthService -> UserRepository -> Database)."""

from __future__ import annotations

from .app import App


def register(app: App) -> None:
    """Register user/auth routes on the app."""

    def register_user(app: App, body: dict) -> dict:
        user = app.services.auth.register(
            email=body.get("email", ""),
            name=body.get("name", ""),
            password=body.get("password", ""),
        )
        return {"status": 201, "user": user.to_dict()}

    def login(app: App, body: dict) -> dict:
        user = app.services.auth.authenticate(
            body.get("email", ""), body.get("password", "")
        )
        if user is None:
            return {"status": 401, "error": "invalid credentials"}
        return {"status": 200, "user": user.to_dict()}

    app.register("POST", "/users", register_user)
    app.register("POST", "/login", login)
