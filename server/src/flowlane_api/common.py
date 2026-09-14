"""Tiny shared helpers: id generation and the clock."""

from datetime import UTC, datetime
from uuid import uuid4


def new_id(prefix: str) -> str:
    """`board-<uuid4>`, `column-<uuid4>`, `task-<uuid4>` — same scheme the frontend mock used."""
    return f"{prefix}-{uuid4()}"


def utcnow() -> datetime:
    return datetime.now(UTC)
