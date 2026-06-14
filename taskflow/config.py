"""Application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Runtime settings for a taskflow application instance."""

    db_path: str = ":memory:"
    secret_key: str = "dev-secret-change-me"
    page_size: int = 20
    token_ttl_seconds: int = 3600

    def with_overrides(self, **kwargs) -> "Settings":
        """Return a copy of these settings with the given fields replaced."""
        data = {**self.__dict__, **kwargs}
        return Settings(**data)


def load_settings() -> Settings:
    """Build Settings from environment variables, falling back to defaults."""
    return Settings(
        db_path=os.environ.get("TASKFLOW_DB", ":memory:"),
        secret_key=os.environ.get("TASKFLOW_SECRET", "dev-secret-change-me"),
        page_size=int(os.environ.get("TASKFLOW_PAGE_SIZE", "20")),
    )
