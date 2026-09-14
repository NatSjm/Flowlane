"""`Store` on top of a SQLAlchemy session.

Records are the session's own ORM instances, so an in-place mutation by a service is
visible to the very next query (autoflush) — the "live records" contract in
`protocols.py`. `add`/`save`/`delete` flush immediately so constraint violations
surface at the call that caused them; the request-level commit lives in
`dependencies.get_store`.

Only portable SQL is used here: no dialect-specific statements, functions, or types.
"""

from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flowlane_api.models import BoardRecord, ColumnRecord, TaskRecord


class SqlBoardRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self) -> list[BoardRecord]:
        stmt = select(BoardRecord).order_by(BoardRecord.created_at, BoardRecord.id)
        return list(self._session.scalars(stmt))

    def get(self, board_id: str) -> BoardRecord | None:
        return self._session.get(BoardRecord, board_id)

    def add(self, board: BoardRecord) -> None:
        self._session.add(board)
        self._session.flush()

    def save(self, board: BoardRecord) -> None:
        self._session.flush()

    def delete(self, board_id: str) -> None:
        board = self._session.get(BoardRecord, board_id)
        if board is not None:
            self._session.delete(board)
            self._session.flush()


class SqlColumnRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, column_id: str) -> ColumnRecord | None:
        return self._session.get(ColumnRecord, column_id)

    def list_for_board(self, board_id: str) -> list[ColumnRecord]:
        stmt = (
            select(ColumnRecord)
            .where(ColumnRecord.board_id == board_id)
            .order_by(ColumnRecord.position, ColumnRecord.id)
        )
        return list(self._session.scalars(stmt))

    def add(self, column: ColumnRecord) -> None:
        self._session.add(column)
        self._session.flush()

    def save(self, column: ColumnRecord) -> None:
        self._session.flush()

    def delete(self, column_id: str) -> None:
        column = self._session.get(ColumnRecord, column_id)
        if column is not None:
            self._session.delete(column)
            self._session.flush()


class SqlTaskRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, task_id: str) -> TaskRecord | None:
        return self._session.get(TaskRecord, task_id)

    def list_for_column(self, column_id: str) -> list[TaskRecord]:
        stmt = (
            select(TaskRecord)
            .where(TaskRecord.column_id == column_id)
            .order_by(TaskRecord.position, TaskRecord.id)
        )
        return list(self._session.scalars(stmt))

    def count_for_columns(self, column_ids: Iterable[str]) -> int:
        wanted = list(column_ids)
        if not wanted:
            return 0
        stmt = select(func.count()).select_from(TaskRecord).where(TaskRecord.column_id.in_(wanted))
        return self._session.scalar(stmt) or 0

    def add(self, task: TaskRecord) -> None:
        self._session.add(task)
        self._session.flush()

    def save(self, task: TaskRecord) -> None:
        self._session.flush()

    def delete(self, task_id: str) -> None:
        task = self._session.get(TaskRecord, task_id)
        if task is not None:
            self._session.delete(task)
            self._session.flush()


class SqlStore:
    """One store per session — i.e. per request; see `dependencies.get_store`."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._boards = SqlBoardRepository(session)
        self._columns = SqlColumnRepository(session)
        self._tasks = SqlTaskRepository(session)

    @property
    def boards(self) -> SqlBoardRepository:
        return self._boards

    @property
    def columns(self) -> SqlColumnRepository:
        return self._columns

    @property
    def tasks(self) -> SqlTaskRepository:
        return self._tasks
