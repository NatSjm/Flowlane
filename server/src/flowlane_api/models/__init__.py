"""ORM models — the rows the repositories store and hand out.

They double as the dataclass "records" the services construct and mutate (the same
attribute names `schemas/` reads via `from_attributes`), so the domain layer never
sees a session. Import `Base` for `metadata` (table creation / migrations).
"""

from flowlane_api.models.base import Base
from flowlane_api.models.boards import BoardRecord
from flowlane_api.models.columns import ColumnRecord
from flowlane_api.models.tasks import TaskRecord

__all__ = ["Base", "BoardRecord", "ColumnRecord", "TaskRecord"]
