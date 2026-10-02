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


class UserService:
    """Manage users while preventing assignment of protected system roles."""

    def __init__(self, db: Session,user_repository:UserRepository,role_repository:RoleRepository):
        self.db = db
        self.user_repository = user_repository
        self.role_repository = role_repository


    def create_user(
        self,
        email: str,
        password: str,
        role_ids: list[int],
    ):
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

        user = self.user_repository.create(
            email=email,
            password_hash=hash_password(password),
        )

        self.user_repository.assign_roles(
            user=user,
            roles=roles,
        )

        self.db.commit()

        return user

    def get_user(self, user_id: int) -> User:
        user = self.user_repository.get_by_id(user_id)

        if not user:
            raise ResourceNotFoundException(
                resource="User",
                resource_id=user_id
            )

        return user

    def update_user(
        self,
        *,
        user_id: int,
        email: str | None,
        password: str | None,
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

        if password is not None:
            user.password_hash = hash_password(password)

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

        self.user_repository.delete(user)
