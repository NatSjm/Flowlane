"""Declarative base + the portable column types the models share.

Models are SQLAlchemy *mapped dataclasses*: they get a keyword-only, type-checked
constructor like the plain dataclasses they replaced, and are also live ORM rows once
added to a session. Nothing here is dialect-specific — the schema must create and
behave identically on SQLite today and PostgreSQL later.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, MetaData
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from sqlalchemy.types import TypeDecorator

# Deterministic constraint names so Alembic migrations can reference them by name on
# every backend (SQLite doesn't name constraints on its own).
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# `board-<uuid4>` etc. (common.new_id) — 36-char uuid plus a short prefix.
ID_LENGTH = 64


class UtcDateTime(TypeDecorator[datetime]):
    """Timestamps are stored as naive UTC and come back tz-aware UTC.

    Storing naive values sidesteps every backend's own timezone handling (SQLite has
    none; PostgreSQL `timestamp` would apply the session zone), so the same code and
    the same rows mean the same instant everywhere.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: Any, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        assert isinstance(value, datetime)
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class Base(MappedAsDataclass, DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
