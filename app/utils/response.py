"""Common API response formatting utilities."""

from typing import Any

from pydantic import BaseModel

from app.schemas.response import ApiResponse


def success_response(
    message: str,
    data: Any = None,
) -> dict[str, Any]:
    """Create a standardized successful API response.

    Pydantic models are converted to dictionaries before being included
    in the response payload.
    """
    if isinstance(data, BaseModel):
        data = data.model_dump()

    return ApiResponse(
        success=True,
        message=message,
        data=data,
    ).model_dump(exclude_none=True)


def error_response(
    message: str,
    errors: Any = None,
) -> dict[str, Any]:
    """Create a standardized error API response.

    The message and optional error details are intended for safe
    client-facing information. Internal exception details should be
    logged separately and should not be exposed here.
    """
    return ApiResponse(
        success=False,
        message=message,
        errors=errors,
    ).model_dump(exclude_none=True)

