"""User repository."""

from __future__ import annotations

from typing import Optional

from ..models.user import User
from .base_repo import BaseRepository


class UserRepository(BaseRepository[User]):
    """Persistence for User entities."""

    table = "users"
    model = User

    def get_by_email(self, email: str) -> Optional[User]:
        """Return the user with the given email, or None."""
        for user in self.list():
            if user.email == email:
                return user
        return None
