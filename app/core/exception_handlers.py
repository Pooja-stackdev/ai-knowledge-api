"""Global FastAPI exception handlers."""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.exceptions import AppException
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
    logger.warning(
        "Application error | path=%s | message=%s",
        request.url.path,
        exc.message,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.message,
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
            "message": error["msg"],
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
            message="Request validation failed",
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
            message="An internal database error occurred",
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
            message="Internal server error",
        ),
    )

