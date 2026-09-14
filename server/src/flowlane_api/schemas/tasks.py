from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import (
    Field,
    ValidationError,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    field_serializer,
    field_validator,
)
from pydantic.alias_generators import to_camel

from flowlane_api.schemas.base import (
    TASK_DESCRIPTION_MAX,
    TASK_TITLE_MAX,
    CamelModel,
    TimestampedModel,
    normalize_datetime,
    to_js_iso,
)


class Priority(StrEnum):
    """One of LOW, MEDIUM, HIGH — kept as an enum end-to-end, never a free string."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Task(TimestampedModel):
    id: str = Field(examples=["task-3f2b1c9a-8e4d-4a11-9b2e-2a6f7d0c9e1a"])
    column_id: str
    title: str
    description: str = Field(description="Empty string when no description has been set.")
    priority: Priority
    position: int = Field(
        ge=0,
        description="Zero-based index within its column; server-maintained.",
    )
    due_date: datetime | None

    @field_serializer("due_date", when_used="json")
    def _serialize_due_date(self, value: datetime | None) -> str | None:
        return None if value is None else to_js_iso(value)


# ---------------------------------------------------------------------------
# Field validators shared by the create and update inputs. They raise ValueError
# with the exact wording of frontend/src/utils/validation.ts so the UI can show
# the server's message verbatim.
# ---------------------------------------------------------------------------


def _validate_title(value: str) -> str:
    # Not `validate_required_name`: the length message says "Title", not "Task title".
    trimmed = value.strip()
    if not trimmed:
        raise ValueError("Task title is required")
    if len(trimmed) > TASK_TITLE_MAX:
        raise ValueError(f"Title must be {TASK_TITLE_MAX} characters or fewer")
    return trimmed


def _validate_description(value: str) -> str:
    trimmed = value.strip()
    if len(trimmed) > TASK_DESCRIPTION_MAX:
        raise ValueError(f"Description must be {TASK_DESCRIPTION_MAX} characters or fewer")
    return trimmed


def _validate_due_date(value: Any, handler: ValidatorFunctionWrapHandler) -> datetime | None:
    try:
        parsed: datetime | None = handler(value)
    except ValidationError:
        raise ValueError("Due date must be a valid date") from None
    return None if parsed is None else normalize_datetime(parsed)


class CreateTaskInput(CamelModel):
    title: str = Field(examples=["Write the API tests"])
    description: str = ""
    priority: Priority = Priority.MEDIUM
    due_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        return _validate_title(value)

    @field_validator("description")
    @classmethod
    def _description(cls, value: str) -> str:
        return _validate_description(value)

    @field_validator("due_date", mode="wrap")
    @classmethod
    def _due_date(cls, value: Any, handler: ValidatorFunctionWrapHandler) -> datetime | None:
        return _validate_due_date(value, handler)


class UpdateTaskInput(CamelModel):
    """Partial update: every field is optional and, when present, replaces the current
    value. Only `dueDate` may be null (to clear it); the others may be omitted but not
    null. Use `model_fields_set` / `model_dump(exclude_unset=True)` to tell "omitted"
    apart from "sent". Supplying `columnId` moves the task to the end of that column.
    """

    title: str | None = None
    description: str | None = None
    priority: Priority | None = None
    due_date: datetime | None = None
    column_id: str | None = Field(
        default=None, description="Move the task to this column (appended at the end)."
    )

    @field_validator("title", "description", "priority", "column_id", mode="before")
    @classmethod
    def _reject_null(cls, value: Any, info: ValidationInfo) -> Any:
        if value is None:
            raise ValueError(f"{to_camel(info.field_name or '')} cannot be null")
        return value

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        return _validate_title(value)

    @field_validator("description")
    @classmethod
    def _description(cls, value: str) -> str:
        return _validate_description(value)

    @field_validator("due_date", mode="wrap")
    @classmethod
    def _due_date(cls, value: Any, handler: ValidatorFunctionWrapHandler) -> datetime | None:
        return _validate_due_date(value, handler)


class MoveTaskInput(CamelModel):
    column_id: str = Field(
        description="Destination column id (may be the task's current column).",
        examples=["column-2"],
    )
    position: int = Field(
        ge=0,
        description=(
            "Desired zero-based index within the destination column's task order. "
            "Out-of-range values are clamped by the server."
        ),
        examples=[1],
    )
