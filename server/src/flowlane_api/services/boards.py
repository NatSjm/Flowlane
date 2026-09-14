from flowlane_api.common import new_id, utcnow
from flowlane_api.errors import NotFoundError
from flowlane_api.models import BoardRecord, ColumnRecord
from flowlane_api.repositories import Store
from flowlane_api.schemas import (
    Board,
    BoardDetail,
    BoardSummary,
    Column,
    ColumnWithTasks,
    CreateBoardInput,
    Task,
    UpdateBoardInput,
)

# No auth yet (openapi.yaml "Authentication"): every board belongs to this one owner.
DEFAULT_OWNER_ID = "local-user"

# Every new board is seeded with these, in this order (_docs/specs.md §2).
DEFAULT_COLUMN_NAMES = ("Todo", "In Progress", "Done")


class BoardService:
    def __init__(self, store: Store) -> None:
        self._store = store

    def list_boards(self) -> list[BoardSummary]:
        summaries: list[BoardSummary] = []
        for board in self._store.boards.list():
            columns = self._store.columns.list_for_board(board.id)
            summaries.append(
                BoardSummary(
                    **Board.model_validate(board).model_dump(),
                    column_count=len(columns),
                    task_count=self._store.tasks.count_for_columns(c.id for c in columns),
                )
            )
        return summaries

    def get_board(self, board_id: str) -> BoardDetail:
        board = self._require_board(board_id)
        columns = [
            ColumnWithTasks(
                **Column.model_validate(column).model_dump(),
                tasks=[
                    Task.model_validate(task)
                    for task in self._store.tasks.list_for_column(column.id)
                ],
            )
            for column in self._store.columns.list_for_board(board.id)
        ]
        return BoardDetail(**Board.model_validate(board).model_dump(), columns=columns)

    def create_board(self, data: CreateBoardInput) -> Board:
        timestamp = utcnow()
        board = BoardRecord(
            id=new_id("board"),
            name=data.name,
            owner_id=DEFAULT_OWNER_ID,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self._store.boards.add(board)
        for position, name in enumerate(DEFAULT_COLUMN_NAMES):
            self._store.columns.add(
                ColumnRecord(
                    id=new_id("column"),
                    board_id=board.id,
                    name=name,
                    position=position,
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
        return Board.model_validate(board)

    def update_board(self, board_id: str, data: UpdateBoardInput) -> Board:
        board = self._require_board(board_id)
        board.name = data.name
        board.updated_at = utcnow()
        self._store.boards.save(board)
        return Board.model_validate(board)

    def delete_board(self, board_id: str) -> None:
        board = self._require_board(board_id)
        for column in self._store.columns.list_for_board(board.id):
            for task in self._store.tasks.list_for_column(column.id):
                self._store.tasks.delete(task.id)
            self._store.columns.delete(column.id)
        self._store.boards.delete(board.id)

    def _require_board(self, board_id: str) -> BoardRecord:
        board = self._store.boards.get(board_id)
        if board is None:
            raise NotFoundError("Board not found")
        return board
