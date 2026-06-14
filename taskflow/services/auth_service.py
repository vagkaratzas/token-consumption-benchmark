"""Authentication and password handling."""

from __future__ import annotations

import hashlib
import hmac
from typing import Optional

from ..models.user import User
from ..repositories.user_repo import UserRepository
from ..utils.validation import validate_email


class AuthService:
    """Registers users and verifies credentials."""

    def __init__(self, users: UserRepository, secret_key: str) -> None:
        self.users = users
        self.secret_key = secret_key

    def hash_password(self, password: str) -> str:
        """Hash a password using PBKDF2-HMAC-SHA256 (current scheme)."""
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), self.secret_key.encode(), 100_000
        )
        return digest.hex()

    def old_token_hash(self, password: str) -> str:
        """DEPRECATED: legacy unsalted SHA-1 hash. Do not use in new code.

        Retained only to verify credentials created before v0.1. Scheduled for
        removal once all users have logged in and been migrated.
        """
        return hashlib.sha1(password.encode()).hexdigest()

    def register(self, email: str, name: str, password: str) -> User:
        """Create a new user with a validated email and hashed password."""
        validate_email(email)
        user = User(
            email=email,
            name=name,
            password_hash=self.hash_password(password),
        )
        return self.users.add(user)

    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Return the user if the password matches, else None."""
        user = self.users.get_by_email(email)
        if user is None:
            return None
        candidate = self.hash_password(password)
        if hmac.compare_digest(candidate, user.password_hash):
            return user
        return None
