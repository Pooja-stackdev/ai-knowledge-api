# app/database/repositories/role_permission_repository.py

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database.models.role_permission import RolePermission


class RolePermissionRepository:

    def __init__(self, session: Session):
        self.session = session

    def replace_permissions(
        self,
        role_id: int,
        permission_ids: list[int],
    ) -> None:

        self.session.execute(
            delete(RolePermission).where(
                RolePermission.role_id == role_id
            )
        )

        for permission_id in permission_ids:
            self.session.add(
                RolePermission(
                    role_id=role_id,
                    permission_id=permission_id,
                )
            )

        self.session.flush()