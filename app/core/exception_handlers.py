"""Global FastAPI exception handlers."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import logging
from app.exceptions import AppException
from app.utils.response import error_response

logger = logging.getLogger(__name__)

async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    """Handle expected application exceptions."""

    logger.warning(
        "Application error: %s",
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
    """Handle FastAPI/Pydantic request validation errors."""

    errors = []

    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(
                    str(location)
                    for location in error["loc"]
                ),
                "message": error["msg"],
            }
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
    """Handle unexpected database errors."""

    logger.exception(
        "Unexpected database error"
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
    """Handle unexpected application errors."""

    logger.exception(
        "Unexpected application error"
    )

    return JSONResponse(
        status_code=500,
        content=error_response(
            message="Internal server error",
        ),
    )

