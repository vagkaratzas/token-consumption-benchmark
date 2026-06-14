"""User domain model."""

from __future__ import annotations

from dataclasses import dataclass

from .base import BaseModel


@dataclass
class User(BaseModel):
    """An account that can own projects and be assigned tasks."""

    email: str = ""
    name: str = ""
    password_hash: str = ""
    role: str = "member"  # one of: member, admin

    def is_admin(self) -> bool:
        """Return True if the user has the admin role."""
        return self.role == "admin"
