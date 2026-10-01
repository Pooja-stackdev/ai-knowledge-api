"""Common application exceptions."""

from app.exceptions.base import AppException


class ResourceNotFoundException(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        resource: str,
        resource_id: int | str,
    ) -> None:
        message_keys = {
            "document": "document.not_found",
            "user": "user.not_found",
            "role": "role.not_found",
            "roles": "role.not_found",
            "one or more": "role.not_found",
        }
        super().__init__(
            message=message_keys.get(resource.lower(), "common.not_found"),
            status_code=404,
        )


class ValidationException(AppException):
    """Raised when business validation fails."""

    def __init__(
        self,
        message: str,
        details: list[str] | dict | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=422,
            details=details,
        )


class ConflictException(AppException):
    """Raised when a request conflicts with the current resource state."""

    def __init__(
        self,
        message: str,
        details: list[str] | dict | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=409,
            details=details,
        )


class UnauthorizedException(AppException):
    """Raised when authentication is required or invalid."""

    def __init__(
        self,
        message: str = "Authentication required",
    ) -> None:
        super().__init__(
            message=message,
            status_code=401,
        )


class ForbiddenException(AppException):
    """Raised when the user is not allowed to perform an operation."""

    def __init__(
        self,
        message: str = "Permission denied",
    ) -> None:
        super().__init__(
            message=message,
            status_code=403,
        )

class BadRequestException(AppException):
    """Raised when the request violates a business rule."""

    def __init__(
        self,
        message: str,
        details: list[str] | dict | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=400,
            details=details,
        )
