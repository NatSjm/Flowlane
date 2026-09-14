from pydantic import Field, field_validator

from flowlane_api.schemas.base import (
    COLUMN_NAME_MAX,
    CamelModel,
    TimestampedModel,
    validate_required_name,
)
from flowlane_api.schemas.tasks import Task


class Column(TimestampedModel):
    id: str = Field(examples=["column-775cc714-7510-4d09-a037-36d6a2c19e27"])
    board_id: str
    name: str
    position: int = Field(
        ge=0, description="Zero-based; server-maintained. Set only via reorder, never directly."
    )


class ColumnWithTasks(Column):
    """A column with its tasks attached, as nested inside `BoardDetail`."""

    tasks: list[Task]


class _ColumnNameInput(CamelModel):
    name: str = Field(examples=["Todo"])

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        return validate_required_name(value, label="Column name", max_length=COLUMN_NAME_MAX)


class CreateColumnInput(_ColumnNameInput):
    pass


class UpdateColumnInput(_ColumnNameInput):
    """Rename only — `name` is required (the frontend sends the full new name)."""


class ReorderColumnsInput(CamelModel):
    column_ids: list[str] = Field(
        description="Every column id on the board, in the desired display order.",
        examples=[["column-3", "column-1", "column-2"]],
    )
