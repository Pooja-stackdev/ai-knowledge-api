from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.models.permission import Permission
from app.database.models.role import Role
from app.database.models.role_permission import RolePermission
from app.database.models.user import User
from app.database.models.user_role import UserRole

PERMISSIONS = [
    {
        "name": "document.create",
        "description": "Create and upload documents",
    },
    {
        "name": "document.read",
        "description": "View documents",
    },
    {
        "name": "document.delete",
        "description": "Delete documents",
    },
    {
        "name": "query.execute",
        "description": "Execute knowledge base queries",
    },
    {
        "name": "user.read",
        "description": "View users",
    },
    {
        "name": "user.create",
        "description": "Create users",
    },
    {
        "name": "user.update",
        "description": "Update users",
    },
    {
        "name": "user.delete",
        "description": "Delete users",
    },
    {
        "name": "role:read",
        "description": "View roles",
    },
    {
        "name": "role:create",
        "description": "Create roles",
    },
    {
        "name": "role:update",
        "description": "Update roles",
    },
    {
        "name": "role:delete",
        "description": "Delete roles",
    },
]


ROLES = [
    {
        "name": "admin",
        "description": "Full system access",
        "permissions": [
            "document.create",
            "document.read",
            "document.delete",
            "query.execute",
            "user.read",
            "user.create",
            "user.update",
            "user.delete",
            "role:read",
            "role:create",
            "role:update",
            "role:delete",
        ],
    },
    {
        "name": "user",
        "description": "Standard knowledge base user",
        "permissions": [
            "document.create",
            "document.read",
            "query.execute",
        ],
    },
]


USERS = [
    {
        "email": "admin@example.com",
        "password": "Admin@123456",
        "role": "admin",
    },
    {
        "email": "user@example.com",
        "password": "User@123456",
        "role": "user",
    },
]


def seed_permissions(session: Session) -> dict[str, Permission]:
    permission_map: dict[str, Permission] = {}

    for data in PERMISSIONS:
        permission = session.scalar(
            select(Permission).where(
                Permission.name == data["name"]
            )
        )

        if permission is None:
            permission = Permission(
                name=data["name"],
                description=data["description"],
            )

            print(permission)
            session.add(permission)
            session.flush()

        permission_map[permission.name] = permission

    return permission_map


def seed_roles(
    session: Session,
    permission_map: dict[str, Permission],
) -> dict[str, Role]:
    role_map: dict[str, Role] = {}

    for data in ROLES:
        role = session.scalar(
            select(Role).where(
                Role.name == data["name"]
            )
        )

        if role is None:
            role = Role(
                name=data["name"],
                description=data["description"],
            )

            session.add(role)
            session.flush()

        for permission_name in data["permissions"]:
            permission = permission_map[permission_name]

            exists = session.scalar(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id,
                )
            )

            if exists is None:
                session.add(
                    RolePermission(
                        role_id=role.id,
                        permission_id=permission.id,
                    )
                )

        role_map[role.name] = role

    session.flush()

    return role_map


def seed_users(
    session: Session,
    role_map: dict[str, Role],
) -> None:
    for data in USERS:
        user = session.scalar(
            select(User).where(
                User.email == data["email"]
            )
        )

        if user is None:
            user = User(
                email=data["email"],
                password_hash=hash_password(data["password"]),
                is_active=True,
            )

            session.add(user)
            session.flush()
        else:
            user.password_hash = hash_password(data["password"])
            user.is_active = True

        role = role_map[data["role"]]

        exists = session.scalar(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
            )
        )

        if exists is None:
            session.add(
                UserRole(
                    user_id=user.id,
                    role_id=role.id,
                )
            )

    session.flush()


def seed_rbac(session: Session) -> None:
    try:
        permission_map = seed_permissions(session)

        role_map = seed_roles(
            session,
            permission_map,
        )

        seed_users(
            session,
            role_map,
        )

        session.commit()

    except Exception:
        session.rollback()
        raise