# app/api/dependencies/document_role.py

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db_session
from app.services.knowledge.document_role_service import (
    DocumentRoleService,
)


def get_document_role_service(
    db: Annotated[Session, Depends(get_db_session)],
) -> DocumentRoleService:
    return DocumentRoleService(db)