from sqlalchemy import ARRAY, Integer, String, cast, distinct, func, literal, select
from sqlalchemy.orm import Session,selectinload

from app.core.rbac import SUPER_ADMIN_ROLE_NAME
from app.database.models.permission import Permission
from app.database.models.role import Role
from app.database.models.user import User
from app.database.models.user_role import UserRole


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
            self, 
            user_id: int,
    ) -> User | None:
        statement = select(User).where(
            User.id == user_id,
        )

        return self.db.scalar(statement)
    
    def _build_user_query(
        self,
        include_roles: bool = False,
        include_permissions: bool = False,
    ):
        statement = select(User)

        if include_roles or include_permissions:
            statement = statement.outerjoin(User.roles)

        if include_permissions:
            statement = statement.outerjoin(Role.permissions)

        if include_roles:
            role_ids = func.array_agg(
                distinct(Role.id)
            ).filter(
                Role.id.is_not(None)
            ).label("role_ids")
        else:
            role_ids = cast(
                None,
                ARRAY(Integer),
            ).label("role_ids")

        if include_permissions:
            permissions = func.array_agg(
                distinct(Permission.name)
            ).filter(
                Permission.name.is_not(None)
            ).label("permissions")
        else:
            permissions = cast(
                None,
                ARRAY(String),
            ).label("permissions")

        statement = statement.add_columns(
            role_ids,
            permissions,
        )

        if include_roles or include_permissions:
            statement = statement.group_by(User.id)

        return statement

    def get_current_user_by_id_with_permissions(self, user_id: int) -> User | None:
        stmt = (
            select(User)
            .options(
                selectinload(User.roles)
                .selectinload(Role.permissions)
            )
            .where(User.id == user_id)
        )

        return self.db.scalar(stmt)

    def get_by_id_with_details(
        self,
        user_id: int,
        include_roles: bool = False,
        include_permissions: bool = False,
    ):
        statement = (
            self._build_user_query(
                include_roles=include_roles,
                include_permissions=include_permissions,
            )
            .where(User.id == user_id)
        )

        return self.db.execute(statement).one_or_none()

    def get_users(
        self,
        include_roles: bool = False,
        include_permissions: bool = False,
    ):
        statement = self._build_user_query(
            include_roles=include_roles,
            include_permissions=include_permissions,
        )

        return self.db.execute(statement).all()

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
        # self.db.commit()
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

    def get_super_admin_user(self) -> User | None:
        statement = (
            select(User)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(Role.name == SUPER_ADMIN_ROLE_NAME)
        )

        return self.db.scalar(statement)