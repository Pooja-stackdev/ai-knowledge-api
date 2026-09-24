"""Common API response schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response structure."""

    success: bool
    message: str
    data: T | None = None
    errors: Any | None = None





