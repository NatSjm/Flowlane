"""Bits every router shares: camelCase path params and documented error responses."""

from typing import Annotated, Any

from fastapi import Path

from flowlane_api.schemas import ErrorResponse

# openapi.yaml names path params in camelCase (`{boardId}`); FastAPI needs the Python
# parameter to carry that alias so the generated schema and the URL template match.
BoardId = Annotated[str, Path(alias="boardId")]
ColumnId = Annotated[str, Path(alias="columnId")]
TaskId = Annotated[str, Path(alias="taskId")]

VALIDATION_ERROR: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "The request body failed validation."}
}
NOT_FOUND: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse, "description": "No record exists for the given id(s)."}
}
