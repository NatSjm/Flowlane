from pydantic import Field, field_validator

from flowlane_api.schemas.base import (
    BOARD_NAME_MAX,
    CamelModel,
    TimestampedModel,
    validate_required_name,
)
from flowlane_api.schemas.columns import ColumnWithTasks


class Board(TimestampedModel):
    id: str = Field(examples=["board-6f7ba813-1720-41f8-a2b7-2d1c516eb287"])
    name: str
    owner_id: str = Field(examples=["local-user"])


class BoardSummary(Board):
    """Board plus aggregate counts, as listed on the `/` dashboard."""

    column_count: int = Field(ge=0)
    task_count: int = Field(ge=0, description="Total tasks across all of the board's columns.")


class BoardDetail(Board):
    """`GET /boards/{boardId}` — columns (by position) each carrying their tasks (by position)."""

    columns: list[ColumnWithTasks]


class _BoardNameInput(CamelModel):
    name: str = Field(examples=["Website Redesign"])

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        return validate_required_name(value, label="Board name", max_length=BOARD_NAME_MAX)


class CreateBoardInput(_BoardNameInput):
    pass


class UpdateBoardInput(_BoardNameInput):
    """Rename only — `name` is required (the frontend sends the full new name)."""
