"""A minimal, framework-free routing app.

Routes are registered as (method, path) -> handler. ``dispatch`` looks up the
handler and calls it with the parsed body. This keeps the
api -> service -> repository -> db call chain explicit and dependency-free
for the benchmark.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional, Tuple

from .deps import Services, build_services

Handler = Callable[["App", dict], dict]


class App:
    """Tiny dispatcher mapping (method, path) to handler functions."""

    def __init__(self, services: Optional[Services] = None) -> None:
        self.services = services or build_services()
        self._routes: Dict[Tuple[str, str], Handler] = {}

    def route(self, method: str, path: str) -> Callable[[Handler], Handler]:
        """Decorator form of route registration."""

        def decorator(fn: Handler) -> Handler:
            self._routes[(method.upper(), path)] = fn
            return fn

        return decorator

    def register(self, method: str, path: str, handler: Handler) -> None:
        """Register a handler for a (method, path) pair."""
        self._routes[(method.upper(), path)] = handler

    def dispatch(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        """Route a request to its handler and return its response dict."""
        handler = self._routes.get((method.upper(), path))
        if handler is None:
            return {"status": 404, "error": "not found"}
        return handler(self, body or {})


def create_app(services: Optional[Services] = None) -> App:
    """Build an App with all routes registered."""
    from . import routes_projects, routes_tasks, routes_users

    app = App(services)
    routes_users.register(app)
    routes_tasks.register(app)
    routes_projects.register(app)
    return app
