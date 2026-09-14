"""Persistence layer.

`protocols.Store` is the interface the services talk to; `sql.SqlStore` implements it
on a SQLAlchemy session (any backend — SQLite today, PostgreSQL later — is a matter of
`DATABASE_URL`). The record classes live in `flowlane_api.models`.
"""

from flowlane_api.models import BoardRecord, ColumnRecord, TaskRecord
from flowlane_api.repositories.protocols import (
    BoardRepository,
    ColumnRepository,
    Store,
    TaskRepository,
)
from flowlane_api.repositories.sql import SqlStore

__all__ = [
    "BoardRecord",
    "BoardRepository",
    "ColumnRecord",
    "ColumnRepository",
    "SqlStore",
    "Store",
    "TaskRecord",
    "TaskRepository",
]
