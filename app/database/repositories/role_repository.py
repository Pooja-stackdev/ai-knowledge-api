# app/database/repositories/role_repository.py

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.role import Role
from app.database.models.user_role import UserRole


class RoleRepository:

    def __init__(self, db: Session):
        self.db = db


    def get_all(self) -> list[Role]:
        return list(
            self.db.scalars(
                select(Role).order_by(Role.name)
            )
        )

    def get_by_name(self, name: str) -> Role | None:
        return self.db.scalar(
            select(Role).where(Role.name == name)
        )

    def create(
        self,
        name: str,
        description: str | None,
    ) -> Role:
        role = Role(
            name=name,
            description=description,
        )

        self.db.add(role)
        self.db.flush()

        return role

    

    def get_by_id(self, role_id: int) -> Role | None:
        return self.db.scalar(
            select(Role).where(Role.id == role_id)
        )


    def update(
        self,
        role: Role,
        name: str,
        description: str | None,
    ) -> Role:
        role.name = name
        role.description = description

        self.db.flush()

        return role


    def delete(self, role: Role) -> None:
        self.db.delete(role)
        self.db.flush()


    def get_role_ids(self, user_id: int) -> list[int]:
        return list(
            self.db.scalars(
                select(UserRole.role_id).where(
                    UserRole.user_id == user_id
                )
            )
        )

    def get_by_ids(self, role_ids: list[int]) -> list[Role]:
        if not role_ids:
            return []

        return list(
            self.db.scalars(
                select(Role).where(Role.id.in_(role_ids))
            ).all()
        )