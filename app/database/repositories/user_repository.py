from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.role import Role
from app.database.models.user import User


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        statement = select(User).where(
            User.id == user_id,
        )

        return self.db.scalar(statement)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(
            User.email == email,
        )

        return self.db.scalar(statement)

    def create(
        self,
        email: str,
        password_hash: str,
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
        )

        self.db.add(user)
        self.db.flush()

        return user

    def assign_roles(
            self,
            user: User,
            roles: list[Role],
        ) -> None:
            user.roles = roles
            self.db.flush()

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.flush()

    def update_password(
        self,
        user: User,
        password_hash: str,
    ) -> User:
        user.password_hash = password_hash

        self.db.commit()
        self.db.refresh(user)

        return user