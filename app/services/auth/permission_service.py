# app/services/rbac/permission_service.py
from sqlalchemy.orm import Session

from app.database.models.permission import Permission
from app.database.repositories.permission_repository import (
    PermissionRepository,
)


class PermissionService:

    def __init__(self, session: Session):
        self.repository = PermissionRepository(session)

    def get_permissions(self) -> list[Permission]:
        return self.repository.get_all()