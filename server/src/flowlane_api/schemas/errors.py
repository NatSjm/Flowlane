from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str = Field(examples=["VALIDATION_ERROR"])
    message: str = Field(examples=["Task title is required"])


class ErrorResponse(BaseModel):
    """`{ "error": { "code", "message" } }` — the envelope every non-2xx response uses."""

    error: ErrorBody
