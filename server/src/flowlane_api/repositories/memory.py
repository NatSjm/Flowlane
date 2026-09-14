"""The mock database: dict-backed, process-local, lost on restart.

Stands in for PostgreSQL until the real persistence layer lands. Records are handed
out by reference, so in-place mutations by the services are immediately visible and
`save` has nothing to do.
"""

from collections.abc import Iterable

from flowlane_api.repositories.records import BoardRecord, ColumnRecord, TaskRecord


class InMemoryBoardRepository:
    def __init__(self) -> None:
        self._boards: dict[str, BoardRecord] = {}

    def list(self) -> list[BoardRecord]:
        return sorted(self._boards.values(), key=lambda b: (b.created_at, b.id))

    def get(self, board_id: str) -> BoardRecord | None:
        return self._boards.get(board_id)

    def add(self, board: BoardRecord) -> None:
        self._boards[board.id] = board

    def save(self, board: BoardRecord) -> None:
        pass

    def delete(self, board_id: str) -> None:
        self._boards.pop(board_id, None)


class InMemoryColumnRepository:
    def __init__(self) -> None:
        self._columns: dict[str, ColumnRecord] = {}

    def get(self, column_id: str) -> ColumnRecord | None:
        return self._columns.get(column_id)

    def list_for_board(self, board_id: str) -> list[ColumnRecord]:
        return sorted(
            (c for c in self._columns.values() if c.board_id == board_id),
            key=lambda c: c.position,
        )

    def add(self, column: ColumnRecord) -> None:
        self._columns[column.id] = column

    def save(self, column: ColumnRecord) -> None:
        pass

    def delete(self, column_id: str) -> None:
        self._columns.pop(column_id, None)


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}

    def get(self, task_id: str) -> TaskRecord | None:
        return self._tasks.get(task_id)

    def list_for_column(self, column_id: str) -> list[TaskRecord]:
        return sorted(
            (t for t in self._tasks.values() if t.column_id == column_id),
            key=lambda t: t.position,
        )

    def count_for_columns(self, column_ids: Iterable[str]) -> int:
        wanted = set(column_ids)
        return sum(1 for t in self._tasks.values() if t.column_id in wanted)

    def add(self, task: TaskRecord) -> None:
        self._tasks[task.id] = task

    def save(self, task: TaskRecord) -> None:
        pass

    def delete(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)


class InMemoryStore:
    def __init__(self) -> None:
        self._boards = InMemoryBoardRepository()
        self._columns = InMemoryColumnRepository()
        self._tasks = InMemoryTaskRepository()

    @property
    def boards(self) -> InMemoryBoardRepository:
        return self._boards

    @property
    def columns(self) -> InMemoryColumnRepository:
        return self._columns

    @property
    def tasks(self) -> InMemoryTaskRepository:
        return self._tasks
