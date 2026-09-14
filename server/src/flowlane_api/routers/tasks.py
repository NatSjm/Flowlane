from typing import Any

from fastapi import APIRouter, Response, status

from flowlane_api.dependencies import TaskServiceDep
from flowlane_api.routers.shared import NOT_FOUND, VALIDATION_ERROR, ColumnId, TaskId
from flowlane_api.schemas import CreateTaskInput, MoveTaskInput, Task, UpdateTaskInput

router = APIRouter(tags=["Tasks"])

TASK_OR_COLUMN_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    404: {**NOT_FOUND[404], "description": "The task, or the target `columnId`, does not exist."}
}


@router.post(
    "/columns/{columnId}/tasks",
    operation_id="createTask",
    summary="Create a task in a column",
    status_code=status.HTTP_201_CREATED,
    responses={**VALIDATION_ERROR, **NOT_FOUND},
)
def create_task(column_id: ColumnId, data: CreateTaskInput, service: TaskServiceDep) -> Task:
    """Appends a new task at the end of the column. `priority` defaults to `MEDIUM`."""
    return service.create_task(column_id, data)


@router.get(
    "/tasks/{taskId}", operation_id="getTask", summary="Get a single task", responses=NOT_FOUND
)
def get_task(task_id: TaskId, service: TaskServiceDep) -> Task:
    return service.get_task(task_id)


@router.patch(
    "/tasks/{taskId}",
    operation_id="updateTask",
    summary="Edit a task",
    responses={**VALIDATION_ERROR, **TASK_OR_COLUMN_NOT_FOUND},
)
def update_task(task_id: TaskId, data: UpdateTaskInput, service: TaskServiceDep) -> Task:
    """All fields are optional — only supplied fields are changed. Setting `columnId`
    moves the task to the end of that column; use `/move` for an exact position."""
    return service.update_task(task_id, data)


@router.delete(
    "/tasks/{taskId}",
    operation_id="deleteTask",
    summary="Delete a task",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
)
def delete_task(task_id: TaskId, service: TaskServiceDep) -> Response:
    """Reindexes the remaining tasks in its column so `position` stays contiguous."""
    service.delete_task(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/tasks/{taskId}/move",
    operation_id="moveTask",
    summary="Move (and/or reorder) a task",
    responses={**VALIDATION_ERROR, **TASK_OR_COLUMN_NOT_FOUND},
)
def move_task(task_id: TaskId, data: MoveTaskInput, service: TaskServiceDep) -> Task:
    """The drag-and-drop endpoint: `position` is the zero-based index within the
    destination column's post-move order (clamped by the server); both the source and
    destination columns are reindexed afterwards."""
    return service.move_task(task_id, data)
