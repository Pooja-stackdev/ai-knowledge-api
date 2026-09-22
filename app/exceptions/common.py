"""Common application exceptions."""

from app.exceptions.base import AppException


class ResourceNotFoundException(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        resource: str,
        resource_id: int | str,
    ):
        super().__init__(
            message=f"{resource} with id '{resource_id}' not found",
            status_code=404,
        )


class ValidationException(AppException):
    """Raised when business validation fails."""

    def __init__(
        self,
        message: str,
        details: list[str] | dict | None = None,
    ):
        super().__init__(
            message=message,
            status_code=422,
            details=details,
        )


class ConflictException(AppException):
    """Raised when a request conflicts with current resource state."""

    def __init__(
        self,
        message: str,
        details: list[str] | dict | None = None,
    ):
        super().__init__(
            message=message,
            status_code=409,
            details=details,
        )


class UnauthorizedException(AppException):
    """Raised when authentication is required or invalid."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=401,
        )


class ForbiddenException(AppException):
    """Raised when the user is not allowed to perform an operation."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            status_code=403,
        )

