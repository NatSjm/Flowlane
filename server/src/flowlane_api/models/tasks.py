from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from flowlane_api.models.base import ID_LENGTH, Base, UtcDateTime
from flowlane_api.schemas.base import TASK_TITLE_MAX
from flowlane_api.schemas.tasks import Priority


class TaskRecord(Base):
    __tablename__ = "tasks"
    # Every read is "this column's tasks, by position".
    __table_args__ = (Index("ix_tasks_column_id_position", "column_id", "position"),)

    id: Mapped[str] = mapped_column(String(ID_LENGTH), primary_key=True)
    column_id: Mapped[str] = mapped_column(
        String(ID_LENGTH), ForeignKey("columns.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(TASK_TITLE_MAX))
    description: Mapped[str] = mapped_column(Text)
    # `native_enum=False` → a plain VARCHAR on every backend, so adding a priority later
    # is a code change rather than a PostgreSQL `ALTER TYPE` migration.
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, native_enum=False, length=16, values_callable=lambda e: [m.value for m in e])
    )
    position: Mapped[int]
    due_date: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime)
