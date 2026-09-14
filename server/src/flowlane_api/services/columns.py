from flowlane_api.common import new_id, utcnow
from flowlane_api.errors import NotFoundError, ValidationError
from flowlane_api.models import ColumnRecord
from flowlane_api.repositories import Store
from flowlane_api.schemas import Column, CreateColumnInput, UpdateColumnInput


class ColumnService:
    def __init__(self, store: Store) -> None:
        self._store = store

    def create_column(self, board_id: str, data: CreateColumnInput) -> Column:
        if self._store.boards.get(board_id) is None:
            raise NotFoundError("Board not found")
        timestamp = utcnow()
        column = ColumnRecord(
            id=new_id("column"),
            board_id=board_id,
            name=data.name,
            # Appended at the end: position = current column count.
            position=len(self._store.columns.list_for_board(board_id)),
            created_at=timestamp,
            updated_at=timestamp,
        )
        self._store.columns.add(column)
        return Column.model_validate(column)

    def update_column(self, column_id: str, data: UpdateColumnInput) -> Column:
        column = self._require_column(column_id)
        column.name = data.name
        column.updated_at = utcnow()
        self._store.columns.save(column)
        return Column.model_validate(column)

    def delete_column(self, column_id: str) -> None:
        column = self._require_column(column_id)
        for task in self._store.tasks.list_for_column(column.id):
            self._store.tasks.delete(task.id)
        self._store.columns.delete(column.id)
        self.reindex_board(column.board_id)

    def reorder_columns(self, board_id: str, column_ids: list[str]) -> list[Column]:
        if self._store.boards.get(board_id) is None:
            raise NotFoundError("Board not found")
        existing = {c.id: c for c in self._store.columns.list_for_board(board_id)}

        # Validate the whole payload before touching anything, so a bad request
        # never leaves the board half-reordered.
        for column_id in column_ids:
            if column_id not in existing:
                raise NotFoundError("Column not found")
        if len(set(column_ids)) != len(column_ids) or set(column_ids) != set(existing):
            raise ValidationError("columnIds must list every column on the board exactly once")

        timestamp = utcnow()
        for position, column_id in enumerate(column_ids):
            column = existing[column_id]
            column.position = position
            column.updated_at = timestamp
            self._store.columns.save(column)
        return [Column.model_validate(c) for c in self._store.columns.list_for_board(board_id)]

    def reindex_board(self, board_id: str) -> None:
        """Make the board's column positions contiguous (0, 1, 2, …) in their current order."""
        for position, column in enumerate(self._store.columns.list_for_board(board_id)):
            if column.position != position:
                column.position = position
                self._store.columns.save(column)

    def _require_column(self, column_id: str) -> ColumnRecord:
        column = self._store.columns.get(column_id)
        if column is None:
            raise NotFoundError("Column not found")
        return column
