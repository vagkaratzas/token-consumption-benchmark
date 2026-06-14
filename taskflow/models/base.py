"""Base model shared by all taskflow domain entities."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BaseModel:
    """Common fields and helpers for every persisted entity."""

    id: Optional[int] = None
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize the model to a plain dict (used by the API layer)."""
        return asdict(self)

    def touch(self) -> None:
        """Mark the entity as modified now."""
        self.updated_at = _utcnow_iso()
