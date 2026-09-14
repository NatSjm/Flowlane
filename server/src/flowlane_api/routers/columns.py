from fastapi import APIRouter, Response, status

from flowlane_api.dependencies import ColumnServiceDep
from flowlane_api.routers.shared import NOT_FOUND, VALIDATION_ERROR, BoardId, ColumnId
from flowlane_api.schemas import (
    Column,
    CreateColumnInput,
    ReorderColumnsInput,
    UpdateColumnInput,
)

router = APIRouter(tags=["Columns"])


@router.post(
    "/boards/{boardId}/columns",
    operation_id="createColumn",
    summary="Create a column on a board",
    status_code=status.HTTP_201_CREATED,
    responses={**VALIDATION_ERROR, **NOT_FOUND},
)
def create_column(board_id: BoardId, data: CreateColumnInput, service: ColumnServiceDep) -> Column:
    """Appends a new column at the end of the board (`position` = current column count)."""
    return service.create_column(board_id, data)


@router.patch(
    "/boards/{boardId}/columns/reorder",
    operation_id="reorderColumns",
    summary="Reorder a board's columns",
    responses={
        **VALIDATION_ERROR,
        404: {
            **NOT_FOUND[404],
            "description": "The board, or one of the ids in `columnIds`, does not exist.",
        },
    },
)
def reorder_columns(
    board_id: BoardId, data: ReorderColumnsInput, service: ColumnServiceDep
) -> list[Column]:
    """`columnIds` must list **every** column on the board, in the desired new order;
    each column's `position` becomes its index in that array."""
    return service.reorder_columns(board_id, data.column_ids)


@router.patch(
    "/columns/{columnId}",
    operation_id="updateColumn",
    summary="Rename a column",
    responses={**VALIDATION_ERROR, **NOT_FOUND},
)
def update_column(
    column_id: ColumnId, data: UpdateColumnInput, service: ColumnServiceDep
) -> Column:
    return service.update_column(column_id, data)


@router.delete(
    "/columns/{columnId}",
    operation_id="deleteColumn",
    summary="Delete a column",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
)
def delete_column(column_id: ColumnId, service: ColumnServiceDep) -> Response:
    """Cascades — deletes every task in the column — then reindexes the board's
    remaining columns so `position` stays contiguous."""
    service.delete_column(column_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
