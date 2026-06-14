"""Input validation helpers."""

from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(ValueError):
    """Raised when user input fails validation."""


def validate_email(email: str) -> str:
    """Return the email if valid, else raise ValidationError."""
    if not _EMAIL_RE.match(email or ""):
        raise ValidationError(f"invalid email: {email!r}")
    return email
