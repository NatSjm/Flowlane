"""Shared model config + validation helpers.

The wire format is camelCase (`boardId`, `createdAt`, …) while Python attributes are
snake_case; `alias_generator=to_camel` bridges the two. Datetimes are emitted exactly
like JavaScript's `Date.prototype.toISOString()` (millisecond precision, `Z` suffix) so
the response looks identical to what the frontend mock produced.
"""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel

# Limits from _docs/specs.md §13 / openapi.yaml (mirrored in frontend/src/utils/validation.ts).
BOARD_NAME_MAX = 100
COLUMN_NAME_MAX = 50
TASK_TITLE_MAX = 200
TASK_DESCRIPTION_MAX = 5000


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class TimestampedModel(CamelModel):
    """Response models carrying `createdAt` / `updatedAt`."""

    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at", when_used="json")
    def _serialize_timestamp(self, value: datetime) -> str:
        return to_js_iso(value)


def to_js_iso(value: datetime) -> str:
    """Format like JS `toISOString()`: `2026-09-14T19:00:00.123Z`."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    utc = value.astimezone(UTC)
    return utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{utc.microsecond // 1000:03d}Z"


def normalize_datetime(value: datetime) -> datetime:
    """Store every datetime as tz-aware UTC; naive input is assumed to be UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def validate_required_name(value: str, *, label: str, max_length: int) -> str:
    """Trim, then enforce non-empty and max length with the frontend's exact messages."""
    trimmed = value.strip()
    if not trimmed:
        raise ValueError(f"{label} is required")
    if len(trimmed) > max_length:
        raise ValueError(f"{label} must be {max_length} characters or fewer")
    return trimmed
