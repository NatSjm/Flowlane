from datetime import datetime

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from flowlane_api.models.base import ID_LENGTH, Base, UtcDateTime
from flowlane_api.schemas.base import COLUMN_NAME_MAX


class ColumnRecord(Base):
    __tablename__ = "columns"
    # Every read is "this board's columns, by position".
    __table_args__ = (Index("ix_columns_board_id_position", "board_id", "position"),)

    id: Mapped[str] = mapped_column(String(ID_LENGTH), primary_key=True)
    # ON DELETE CASCADE is a safety net; the services still delete children explicitly.
    board_id: Mapped[str] = mapped_column(
        String(ID_LENGTH), ForeignKey("boards.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(COLUMN_NAME_MAX))
    position: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(UtcDateTime)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime)
