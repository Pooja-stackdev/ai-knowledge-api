from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.documents import router as document_router
from app.core.config import settings
from app.core.exception_handlers import (
    app_exception_handler,
    database_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging
from app.exceptions import AppException

setup_logging()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)


app.include_router(document_router)


app.add_exception_handler(
    AppException,
    app_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    SQLAlchemyError,
    database_exception_handler,
)

app.add_exception_handler(
    Exception,
    generic_exception_handler,
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "environment": settings.environment,
    }