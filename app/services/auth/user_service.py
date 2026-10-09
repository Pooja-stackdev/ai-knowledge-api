from sqlalchemy.orm import Session

from app.core.rbac import PROTECTED_ROLE_NAMES
from app.core.security import (
    hash_password,
)
from app.database.models.user import User
from app.database.repositories.role_repository import RoleRepository
from app.database.repositories.user_repository import UserRepository
from app.exceptions.common import (
    BadRequestException,
    ConflictException,
    ResourceNotFoundException,
)
from app.schemas.user import UserResponse
from app.services.auth.authorization_service import AuthorizationService


class UserService:
    """Manage users while preventing assignment of protected system roles."""

    def __init__(self, db: Session,user_repository:UserRepository,role_repository:RoleRepository,authorization_service:AuthorizationService):
        self.db = db
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.authorization_service = authorization_service


    def create_user(
        self,
        email: str,
        password: str,
        role_ids: list[int],
    ) -> UserResponse:
        existing_user = self.user_repository.get_by_email(email)

        if existing_user is not None:
            raise ConflictException("User already exists")

        roles = self.role_repository.get_by_ids(role_ids)

        if len(roles) != len(set(role_ids)):
            raise ConflictException("One or more roles do not exist")

        for role in roles:
            if role.name in PROTECTED_ROLE_NAMES:
                raise ConflictException(
                    "user.super_admin_assignment_forbidden"
                )

        try:
            user = self.user_repository.create(
                email=email,
                password_hash=hash_password(password),
            )

            self.user_repository.assign_roles(
                user=user,
                roles=roles,
            )

            self.db.commit()
            self.db.refresh(user)

            return UserResponse(
                id=user.id,
                email=user.email,
                is_active=user.is_active,
                role_ids=[role.id for role in user.roles],
                permissions=[
                    permission.name
                    for role in user.roles
                    for permission in role.permissions
                ],
            )

        except Exception:
            self.db.rollback()
            raise

    def get_user(
        self,
        user_id: int,
        current_user: User,
    ) -> UserResponse:

        can_read_roles = self.authorization_service.has_permission(
            current_user,
            "role.read",
        )

        can_read_permissions = self.authorization_service.has_permission(
            current_user,
            "permission.read",
        )

        result = self.user_repository.get_by_id_with_details(
            user_id=user_id,
            include_roles=can_read_roles,
            include_permissions=can_read_permissions,
        )

        if result is None:
            raise ResourceNotFoundException(
                resource="User",
                resource_id=user_id,
            )

        user, role_ids, permissions = result

        if not user.is_active:
            raise ResourceNotFoundException(
                resource="User",
                resource_id=user_id,
            )

        return UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            role_ids=role_ids or [],
            permissions=permissions or [],
        )

    def update_user(
        self,
        *,
        user_id: int,
        email: str | None,
        role_ids: list[int] | None,
    ) -> User:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException(
                resource="User",
                resource_id=user_id
            )

        if email is not None:
            existing_user = self.user_repository.get_by_email(email)
            if existing_user and existing_user.id != user.id:
                raise ConflictException(
                    "User with this email already exists"
                )

            user.email = email

        if role_ids is not None:
            roles = self.role_repository.get_by_ids(role_ids)

            if len(roles) != len(set(role_ids)):
                raise ResourceNotFoundException(
                    resource="Roles",
                    resource_id=role_ids
                )

            for role in roles:
                if role.name in PROTECTED_ROLE_NAMES:
                    raise BadRequestException(
                        "user.super_admin_assignment_forbidden"
                    )
            user.roles = roles

        self.db.commit()
        self.db.refresh(user)

        return user

    def delete_user(self, user_id: int) -> None:
        user = self.user_repository.get_by_id(user_id)

        if not user:
            raise ResourceNotFoundException(
                resource="User",
                resource_id=user_id
            )

        try:
            self.user_repository.delete(user)
            self.user_repository.db.commit()
        except Exception:
            self.user_repository.db.rollback()
            raise

    def get_users(self, current_user: User) -> list[UserResponse]:
        can_read_roles = self.authorization_service.has_permission(
            current_user,
            "role.read",
        )

        can_read_permissions = self.authorization_service.has_permission(
            current_user,
            "permission.read",
        )

        rows = self.user_repository.get_users(
            include_roles=can_read_roles,
            include_permissions=can_read_permissions,
        )

        return [
            UserResponse(
                id=user.id,
                email=user.email,
                is_active=user.is_active,
                role_ids=role_ids or [],
                permissions=permissions or []
            )
            for user, role_ids,permissions in rows
        ]