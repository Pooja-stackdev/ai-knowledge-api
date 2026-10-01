# app/api/dependencies/permission.py

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db_session
from app.services.auth.permission_service import PermissionService


def get_permission_service(
    session: Annotated[
        Session,
        Depends(get_db_session),
    ],
) -> PermissionService:
    return PermissionService(session)