from fastapi import APIRouter, Response, status

from flowlane_api.dependencies import BoardServiceDep
from flowlane_api.routers.shared import NOT_FOUND, VALIDATION_ERROR, BoardId
from flowlane_api.schemas import (
    Board,
    BoardDetail,
    BoardSummary,
    CreateBoardInput,
    UpdateBoardInput,
)

router = APIRouter(prefix="/boards", tags=["Boards"])


@router.get("", operation_id="listBoards", summary="List boards")
def list_boards(service: BoardServiceDep) -> list[BoardSummary]:
    """One summary per board with aggregate column/task counts, oldest-created first."""
    return service.list_boards()


@router.post(
    "",
    operation_id="createBoard",
    summary="Create a board",
    status_code=status.HTTP_201_CREATED,
    responses=VALIDATION_ERROR,
)
def create_board(data: CreateBoardInput, service: BoardServiceDep) -> Board:
    """Creates a board seeded with the default **Todo / In Progress / Done** columns."""
    return service.create_board(data)


@router.get(
    "/{boardId}",
    operation_id="getBoard",
    summary="Get a board's full detail",
    responses=NOT_FOUND,
)
def get_board(board_id: BoardId, service: BoardServiceDep) -> BoardDetail:
    """The board with its columns (by position), each carrying its tasks (by position)."""
    return service.get_board(board_id)


@router.patch(
    "/{boardId}",
    operation_id="updateBoard",
    summary="Rename a board",
    responses={**VALIDATION_ERROR, **NOT_FOUND},
)
def update_board(board_id: BoardId, data: UpdateBoardInput, service: BoardServiceDep) -> Board:
    return service.update_board(board_id, data)


@router.delete(
    "/{boardId}",
    operation_id="deleteBoard",
    summary="Delete a board",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
)
def delete_board(board_id: BoardId, service: BoardServiceDep) -> Response:
    """Cascades — deletes every column and task belonging to the board."""
    service.delete_board(board_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
