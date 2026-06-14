"""Command-line interface for taskflow (cli -> services -> repos -> db)."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .api.deps import Services, build_services


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(prog="taskflow", description="Task management CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_user = sub.add_parser("create-user", help="Register a new user")
    p_user.add_argument("email")
    p_user.add_argument("name")
    p_user.add_argument("password")

    p_proj = sub.add_parser("create-project", help="Create a project")
    p_proj.add_argument("name")
    p_proj.add_argument("owner_id", type=int)

    p_task = sub.add_parser("create-task", help="Create a task")
    p_task.add_argument("title")
    p_task.add_argument("project_id", type=int)
    p_task.add_argument("--assignee", type=int, default=None)

    return parser


def main(argv: Optional[List[str]] = None, services: Optional[Services] = None) -> int:
    """Entry point for the CLI. Returns a process exit code."""
    args = build_parser().parse_args(argv)
    services = services or build_services()

    if args.command == "create-user":
        user = services.auth.register(args.email, args.name, args.password)
        print(f"created user {user.id}: {user.email}")
    elif args.command == "create-project":
        project = services.projects.create_project(args.name, args.owner_id)
        print(f"created project {project.id}: {project.name}")
    elif args.command == "create-task":
        task = services.tasks.create_task(args.title, args.project_id, args.assignee)
        print(f"created task {task.id}: {task.title}")
    else:  # pragma: no cover
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
