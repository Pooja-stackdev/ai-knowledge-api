"""Database-related application exceptions."""

from app.exceptions.base import AppException


class DatabaseErrorException(AppException):
    """Raised when an unexpected database error occurs."""

    def __init__(
        self,
        details: list[str] | dict | None = None,
    ):
        super().__init__(
            message="An internal database error occurred",
            status_code=500,
            details=details,
        )
