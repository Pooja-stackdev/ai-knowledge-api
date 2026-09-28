"""Authentication and authorization exceptions."""

from fastapi import status

from app.exceptions.base import AppException


class AuthenticationException(AppException):
    """Raised when a user cannot be authenticated."""

    def __init__(
        self,
        message: str = "Authentication failed.",
        details: list[str] | dict | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class AuthorizationException(AppException):
    """Raised when an authenticated user lacks permission."""

    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        details: list[str] | dict | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )