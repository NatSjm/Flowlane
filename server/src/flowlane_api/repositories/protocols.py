"""Repository interfaces.

Records returned by `get`/`list*` are live: services mutate them in place and call
`save` so a database-backed implementation can flush the change. (The in-memory store's
`save` is a no-op because it hands out its own objects.) Cascading deletes are
orchestrated by the services, not hidden in the repositories, so they stay explicit.
"""

from collections.abc import Iterable
from typing import Protocol

from flowlane_api.repositories.records import BoardRecord, ColumnRecord, TaskRecord


class BoardRepository(Protocol):
    def list(self) -> list[BoardRecord]:
        """All boards, oldest-created first."""
        ...

    def get(self, board_id: str) -> BoardRecord | None: ...

    def add(self, board: BoardRecord) -> None: ...

    def save(self, board: BoardRecord) -> None: ...

    def delete(self, board_id: str) -> None: ...


class ColumnRepository(Protocol):
    def get(self, column_id: str) -> ColumnRecord | None: ...

    def list_for_board(self, board_id: str) -> list[ColumnRecord]:
        """A board's columns sorted by `position` ascending."""
        ...

    def add(self, column: ColumnRecord) -> None: ...

    def save(self, column: ColumnRecord) -> None: ...

    def delete(self, column_id: str) -> None: ...


class TaskRepository(Protocol):
    def get(self, task_id: str) -> TaskRecord | None: ...

    def list_for_column(self, column_id: str) -> list[TaskRecord]:
        """A column's tasks sorted by `position` ascending."""
        ...

    def count_for_columns(self, column_ids: Iterable[str]) -> int: ...

    def add(self, task: TaskRecord) -> None: ...

    def save(self, task: TaskRecord) -> None: ...

    def delete(self, task_id: str) -> None: ...


class Store(Protocol):
    """The unit the services depend on: one repository per aggregate."""

    @property
    def boards(self) -> BoardRepository: ...

    @property
    def columns(self) -> ColumnRepository: ...

    @property
    def tasks(self) -> TaskRepository: ...
