"""Persistence layer.

`protocols.Store` is the interface the services talk to; `memory.InMemoryStore` is the
mock database used today. A SQLAlchemy/PostgreSQL implementation of the same protocol
will replace it later without touching `services/` or `routers/`.
"""

from flowlane_api.repositories.protocols import (
    BoardRepository,
    ColumnRepository,
    Store,
    TaskRepository,
)
from flowlane_api.repositories.records import BoardRecord, ColumnRecord, TaskRecord

__all__ = [
    "BoardRecord",
    "BoardRepository",
    "ColumnRecord",
    "ColumnRepository",
    "Store",
    "TaskRecord",
    "TaskRepository",
]
