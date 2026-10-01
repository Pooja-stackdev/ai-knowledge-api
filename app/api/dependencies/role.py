# app/api/dependencies/role.py

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db_session
from app.database.repositories.role_repository import RoleRepository
from app.services.auth.role_service import RoleService


def get_role_service(
    db: Annotated[Session, Depends(get_db_session)],
) -> RoleService:
    return RoleService(db)


def get_user_role_repository(
    db: Annotated[Session, Depends(get_db_session)],
) -> RoleRepository:
    return RoleRepository(db)