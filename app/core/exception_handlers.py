"""Global FastAPI exception handlers."""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.exceptions import AppException
from app.core.i18n import get_message, localize_message
from app.utils.response import error_response

logger = logging.getLogger(__name__)


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    """Handle expected application exceptions.

    Application exceptions represent known business or application
    errors and are returned to the client using their configured
    HTTP status code and error details.
    """
    headers = {}

    if exc.status_code == 401:
        headers["WWW-Authenticate"] = "Bearer"

    logger.warning(
        "Application error | path=%s | message=%s",
        request.url.path,
        exc.message,
    )

    return JSONResponse(
        status_code=exc.status_code,
        headers=headers,
        content=error_response(
            message=localize_message(exc.message),
            errors=exc.details,
        ),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle request validation errors raised by FastAPI/Pydantic.

    Validation errors are expected client-side errors and therefore
    do not require an exception traceback.
    """
    errors = [
        {
            "field": ".".join(str(location) for location in error["loc"]),
            "message": _localize_validation_error(error),
        }
        for error in exc.errors()
    ]

    logger.warning(
        "Request validation failed | path=%s | errors=%s",
        request.url.path,
        len(errors),
    )

    return JSONResponse(
        status_code=422,
        content=error_response(
            message=get_message("validation.request_failed"),
            errors=errors,
        ),
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """Handle unexpected SQLAlchemy database errors.

    The exception details are logged internally while a generic
    message is returned to avoid exposing database information.
    """
    logger.exception(
        "Unexpected database error | path=%s",
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content=error_response(
            message=get_message("common.database_error"),
        ),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected application errors.

    The full traceback is logged internally while a generic response
    is returned to the client.
    """
    logger.exception(
        "Unexpected application error | path=%s",
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content=error_response(
            message=get_message("common.internal_error"),
        ),
    )


def _localize_validation_error(error: dict) -> str:
    """Map stable Pydantic error types to localized client messages."""
    error_type = error.get("type", "")
    if error_type == "missing":
        return get_message("validation.required")
    if error_type in {"string_too_short", "too_short"}:
        return get_message("validation.min_length")
    return get_message("validation.invalid")

