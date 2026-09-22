
"""Common API response formatting utilities."""

from typing import Any

from pydantic import BaseModel

from app.schemas.response import ApiResponse


def success_response(
    message: str,
    data: Any = None,
) -> dict:
    """Create a standard successful API response."""

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
) -> dict:
    """Create a standard error API response."""

    return ApiResponse(
        success=False,
        message=message,
        errors=errors,
    ).model_dump(exclude_none=True)
