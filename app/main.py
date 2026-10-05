"""FastAPI application entry point."""

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.auth import router as auth_router
from app.api.routes.documents import router as document_router
from app.api.routes.permissions import router as permission_route
from app.api.routes.query import router as query_router
from app.api.routes.roles import router as role_router
from app.api.routes.users import router as user_router
from app.core.config import settings
from app.core.exception_handlers import (
    app_exception_handler,
    database_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from app.core.i18n.middleware import localization_middleware
from app.core.logging import setup_logging
from app.database.connection import SessionLocal
from app.exceptions import AppException

setup_logging()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.middleware("http")(localization_middleware)


@app.get("/health/live", tags=["Health"])
def liveness() -> dict[str, str]:
    """Public liveness probe that does not depend on external services."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["Health"])
def readiness() -> dict[str, str]:
    """Public readiness probe that verifies database connectivity."""
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Service unavailable") from exc
    return {"status": "ready"}

app.include_router(auth_router)
app.include_router(document_router)
app.include_router(query_router)
app.include_router(role_router)
app.include_router(user_router)
app.include_router(permission_route)


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

