"""Schema-level guarantees of the ORM models, exercised directly through a session
(no HTTP): timezone handling, foreign keys, and the ON DELETE CASCADE safety net."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flowlane_api.db import create_db_engine, create_session_factory, init_db
from flowlane_api.models import BoardRecord, ColumnRecord, TaskRecord
from flowlane_api.schemas.tasks import Priority

NOW = datetime(2026, 9, 14, 12, 0, 0, 123000, tzinfo=UTC)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_db_engine("sqlite://")
    init_db(engine)
    with create_session_factory(engine)() as session:
        yield session
    engine.dispose()


def _board(session: Session, board_id: str = "board-1") -> BoardRecord:
    board = BoardRecord(id=board_id, name="B", owner_id="o", created_at=NOW, updated_at=NOW)
    session.add(board)
    session.flush()
    return board


def _column(session: Session, board_id: str, column_id: str = "column-1") -> ColumnRecord:
    column = ColumnRecord(
        id=column_id, board_id=board_id, name="C", position=0, created_at=NOW, updated_at=NOW
    )
    session.add(column)
    session.flush()
    return column


def _task(
    session: Session,
    column_id: str,
    task_id: str = "task-1",
    *,
    priority: Priority = Priority.MEDIUM,
    due_date: datetime | None = None,
) -> TaskRecord:
    task = TaskRecord(
        id=task_id,
        column_id=column_id,
        title="T",
        description="",
        priority=priority,
        position=0,
        due_date=due_date,
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(task)
    session.flush()
    return task


def _reload(session: Session, task_id: str) -> TaskRecord:
    """Read the row back from the database, not the identity map."""
    session.commit()
    session.expunge_all()
    task = session.get(TaskRecord, task_id)
    assert task is not None
    return task


# --- timestamps -------------------------------------------------------------


def test_timestamps_come_back_tz_aware_utc(session: Session) -> None:
    _column(session, _board(session).id)
    _task(session, "column-1")

    task = _reload(session, "task-1")

    assert task.created_at == NOW
    assert task.created_at.tzinfo is UTC
    assert task.created_at.microsecond == 123000, "sub-second precision is preserved"


def test_non_utc_offsets_are_normalized_to_utc(session: Session) -> None:
    _column(session, _board(session).id)
    plus_two = datetime(2026, 10, 1, 14, 0, tzinfo=timezone(timedelta(hours=2)))
    _task(session, "column-1", due_date=plus_two)

    task = _reload(session, "task-1")

    assert task.due_date == datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
    assert task.due_date.utcoffset() == timedelta(0)


def test_naive_datetimes_are_treated_as_utc(session: Session) -> None:
    _column(session, _board(session).id)
    _task(session, "column-1", due_date=datetime(2026, 10, 1, 12, 0))

    task = _reload(session, "task-1")

    assert task.due_date == datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


def test_null_due_date_round_trips(session: Session) -> None:
    _column(session, _board(session).id)
    _task(session, "column-1", due_date=None)

    assert _reload(session, "task-1").due_date is None


def test_priority_is_stored_as_its_value(session: Session) -> None:
    _column(session, _board(session).id)
    _task(session, "column-1", priority=Priority.HIGH)

    task = _reload(session, "task-1")
    assert task.priority is Priority.HIGH
    # Raw column value is the plain string — portable, no native enum type.
    raw = session.execute(select(TaskRecord.__table__.c.priority)).scalar_one()
    assert raw == "HIGH"


# --- referential integrity --------------------------------------------------


def test_foreign_keys_are_enforced(session: Session) -> None:
    # SQLite only enforces them with PRAGMA foreign_keys=ON, which db.py turns on.
    with pytest.raises(IntegrityError):
        _column(session, board_id="board-does-not-exist")
    session.rollback()

    _column(session, _board(session).id)
    with pytest.raises(IntegrityError):
        _task(session, column_id="column-does-not-exist")


def test_deleting_a_board_row_cascades_to_columns_and_tasks(session: Session) -> None:
    """The services delete children explicitly; the database does too, as a safety net."""
    board = _board(session)
    other = _board(session, "board-2")
    _column(session, board.id, "column-1")
    _column(session, other.id, "column-2")
    _task(session, "column-1", "task-1")
    _task(session, "column-2", "task-2")

    session.delete(board)
    session.commit()
    session.expunge_all()

    assert session.get(ColumnRecord, "column-1") is None
    assert session.get(TaskRecord, "task-1") is None
    assert session.get(ColumnRecord, "column-2") is not None
    assert session.get(TaskRecord, "task-2") is not None
