"""Generic repository implementing CRUD over the Database."""

from __future__ import annotations

from dataclasses import asdict
from typing import Generic, List, Optional, Type, TypeVar

from ..db import Database
from ..models.base import BaseModel

M = TypeVar("M", bound=BaseModel)


class BaseRepository(Generic[M]):
    """Maps domain models to/from rows in a single Database table."""

    table: str = ""
    model: Type[M]

    def __init__(self, db: Database) -> None:
        self.db = db

    def _to_model(self, row: Optional[dict]) -> Optional[M]:
        if row is None:
            return None
        return self.model(**row)

    def add(self, entity: M) -> M:
        """Persist a new entity and return it with its assigned id."""
        row = asdict(entity)
        row.pop("id", None)
        entity.id = self.db.insert(self.table, row)
        return entity

    def get(self, entity_id: int) -> Optional[M]:
        """Fetch a single entity by id, or None."""
        return self._to_model(self.db.get(self.table, entity_id))

    def list(self) -> List[M]:
        """Return all entities in the table."""
        return [self._to_model(r) for r in self.db.list(self.table)]

    def update(self, entity_id: int, changes: dict) -> Optional[M]:
        """Apply partial changes and return the updated entity, or None."""
        return self._to_model(self.db.update(self.table, entity_id, changes))

    def remove(self, entity_id: int) -> bool:
        """Delete an entity by id. Returns True if removed."""
        return self.db.delete(self.table, entity_id)
