# app/services/rbac/role_service.py

from sqlalchemy.orm import Session

from app.database.models.role_permission import RolePermission
from app.database.repositories.permission_repository import (
    PermissionRepository,
)
from app.database.repositories.role_permission_repository import (
    RolePermissionRepository,
)
from app.database.repositories.role_repository import (
    RoleRepository,
)
from app.exceptions.common import (
    BadRequestException,
    ResourceNotFoundException,
    ValidationException,
)


class RoleService:

    def __init__(self, db: Session):
        self.db = db
        self.role_repository = RoleRepository(db)
        self.permission_repository = PermissionRepository(db)
        self.role_permission_repository  = RolePermissionRepository(db)

    def create_role(
        self,
        name: str,
        description: str | None,
        permission_ids: list[int],
    ):

        existing_role = self.role_repository.get_by_name(name)

        if existing_role is not None:
            raise BadRequestException("Role already exists")

        permission_ids = list(set(permission_ids))

        permissions = self.permission_repository.get_by_ids(
            permission_ids
        )

        if len(permissions) != len(permission_ids):
            raise ResourceNotFoundException(
                resource="One or More",
                resource_id=permission_ids,
            )

        role = self.role_repository.create(
            name=name,
            description=description,
        )

        for permission in permissions:
            self.db.add(
                RolePermission(
                    role_id=role.id,
                    permission_id=permission.id,
                )
            )

        self.db.commit()

        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permission_ids": permission_ids,
        }


    def get_roles(self) -> list[dict]:
        roles = self.role_repository.get_all()
        return [
            {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "permission_ids": [
                    Permission.id
                    for Permission in role.permissions
                ],
            }
            for role in roles
        ]

    def get_role(self, role_id: int) -> dict:
        role = self.role_repository.get_by_id(role_id)

        if role is None:
            raise ResourceNotFoundException(
                resource="Role",
                resource_id=role_id,
            )

        permission_ids = [
            Permission.id
            for Permission in role.permissions
        ]

        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permission_ids": permission_ids,
        }



    def update_role(
        self,
        role_id: int,
        name: str,
        description: str | None,
        permission_ids: list[int],
    ):
        role = self.role_repository.get_by_id(role_id)

        if role is None:
            raise ResourceNotFoundException(
                resource="Role",
                resource_id=role_id,
            )

        existing_role = self.role_repository.get_by_name(name)

        if existing_role is not None and existing_role.id != role_id:
            raise ValueError("Role name already exists")

        permission_ids = list(set(permission_ids))

        if role.name == "admin":
            admin_permission_ids = {
                permission.id
                for permission in self.permission_repository.get_all()
            }

            if not admin_permission_ids.issubset(
                set(permission_ids)
            ):
                raise ValidationException(
                    "Admin role must retain all permissions"
                )

        permissions = self.permission_repository.get_by_ids(
            permission_ids
        )

        if len(permissions) != len(permission_ids):
            raise ResourceNotFoundException(
                resource="Permissions",
                resource_id=permission_ids,
            )

        self.role_repository.update(
            role=role,
            name=name,
            description=description,
        )

        self.role_permission_repository.replace_permissions(
            role_id=role_id,
            permission_ids=permission_ids,
        )

        self.db.commit()

        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permission_ids": permission_ids,
        }

    def delete_role(self, role_id: int) -> None:
        role = self.role_repository.get_by_id(role_id)

        if role is None:
            raise ResourceNotFoundException(
                resource="Role",
                resource_id=role_id,
            )

        if role.name == "admin":
            raise ValidationException(
                "The admin role cannot be deleted"
            )

        self.role_repository.delete(role)

        self.db.commit()