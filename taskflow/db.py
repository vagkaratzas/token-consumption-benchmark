"""A tiny in-memory database used by the repository layer.

This is deliberately framework-free so the benchmark has a clear, traceable
call chain:  api -> service -> repository -> Database.
"""

from __future__ import annotations

import itertools
from typing import Dict, List, Optional


class Database:
    """In-memory table store keyed by table name then row id."""

    def __init__(self) -> None:
        self._tables: Dict[str, Dict[int, dict]] = {}
        self._ids = itertools.count(1)

    def _table(self, name: str) -> Dict[int, dict]:
        return self._tables.setdefault(name, {})

    def insert(self, table: str, row: dict) -> int:
        """Insert a row, assigning a fresh integer id. Returns the new id."""
        row_id = next(self._ids)
        stored = dict(row)
        stored["id"] = row_id
        self._table(table)[row_id] = stored
        return row_id

    def get(self, table: str, row_id: int) -> Optional[dict]:
        """Return a copy-safe reference to a stored row, or None."""
        return self._table(table).get(row_id)

    def list(self, table: str) -> List[dict]:
        """Return all rows in a table."""
        return list(self._table(table).values())

    def update(self, table: str, row_id: int, changes: dict) -> Optional[dict]:
        """Apply partial changes to a row. Returns the row, or None if absent."""
        row = self._table(table).get(row_id)
        if row is None:
            return None
        row.update(changes)
        return row

    def delete(self, table: str, row_id: int) -> bool:
        """Delete a row. Returns True if a row was removed."""
        return self._table(table).pop(row_id, None) is not None
