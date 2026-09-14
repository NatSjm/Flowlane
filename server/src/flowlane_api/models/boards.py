from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from flowlane_api.models.base import ID_LENGTH, Base, UtcDateTime
from flowlane_api.schemas.base import BOARD_NAME_MAX


class BoardRecord(Base):
    __tablename__ = "boards"

    id: Mapped[str] = mapped_column(String(ID_LENGTH), primary_key=True)
    name: Mapped[str] = mapped_column(String(BOARD_NAME_MAX))
    # No users table until auth lands (openapi.yaml "Authentication"), so this is a
    # plain string rather than a foreign key for now.
    owner_id: Mapped[str] = mapped_column(String(ID_LENGTH))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime)
