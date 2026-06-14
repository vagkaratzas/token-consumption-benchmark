"""Project domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .base import BaseModel


@dataclass
class Project(BaseModel):
    """A container of tasks owned by a user and shared with members."""

    name: str = ""
    owner_id: Optional[int] = None
    member_ids: List[int] = field(default_factory=list)

    def add_member(self, user_id: int) -> None:
        """Add a member id if not already present."""
        if user_id not in self.member_ids:
            self.member_ids.append(user_id)
