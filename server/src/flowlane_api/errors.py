"""Domain exceptions and the FastAPI handlers that turn every failure into the
`{ "error": { "code", "message" } }` envelope from openapi.yaml / specs §14."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    """Base for errors the services raise deliberately; carries the wire code + status."""

    status_code: int
    code: str

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(ApiError):
    status_code = 404
    code = "NOT_FOUND"


class ValidationError(ApiError):
    """A request that is well-formed but violates a business rule (e.g. reorder
    payload doesn't list every column). Shape-level errors are Pydantic's job."""

    status_code = 400
    code = "VALIDATION_ERROR"


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"error": {"code": code, "message": message}}
    )


def _validation_message(errors: list[dict[str, Any]]) -> str:
    """Pick a single human-readable message from Pydantic's error list.

    Validators in `schemas/` raise `ValueError` with the exact wording the
    frontend's `validation.ts` uses ("Task title is required", …); Pydantic
    prefixes those with "Value error, ", which we strip so the UI can show the
    message verbatim. Anything else (missing field, wrong type, bad enum) gets a
    generic "<field>: <reason>" message.
    """
    if not errors:
        return "Invalid request"
    first = errors[0]
    msg: str = first.get("msg", "Invalid value")
    if first.get("type") == "value_error":
        return msg.removeprefix("Value error, ")
    if first.get("type") == "json_invalid":
        return "Request body is not valid JSON"
    loc = [part for part in first.get("loc", ()) if part != "body"]
    field = ".".join(str(part) for part in loc)
    return f"{field}: {msg}" if field else msg


_HTTP_CODES = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_: Request, exc: ApiError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # openapi.yaml documents body validation failures as 400, not FastAPI's default 422.
        return error_response(400, "VALIDATION_ERROR", _validation_message(list(exc.errors())))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Unknown routes, wrong methods, etc. — keep the same envelope.
        code = _HTTP_CODES.get(exc.status_code, "HTTP_ERROR")
        return error_response(exc.status_code, code, str(exc.detail))

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        return error_response(500, "INTERNAL_ERROR", "Internal server error")
