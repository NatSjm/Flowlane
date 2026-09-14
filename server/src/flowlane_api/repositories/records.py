"""Persistence-level records (what a repository stores and returns).

Deliberately plain dataclasses rather than Pydantic models: they're the internal shape
(the future ORM rows will be mapped to/from these), while `schemas/` is the wire shape.
"""

from dataclasses import dataclass
from datetime import datetime

from flowlane_api.schemas.tasks import Priority


@dataclass
class BoardRecord:
    id: str
    name: str
    owner_id: str
    created_at: datetime
    updated_at: datetime


@dataclass
class ColumnRecord:
    id: str
    board_id: str
    name: str
    position: int
    created_at: datetime
    updated_at: datetime


@dataclass
class TaskRecord:
    id: str
    column_id: str
    title: str
    description: str
    priority: Priority
    position: int
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
