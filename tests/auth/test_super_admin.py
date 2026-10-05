"""RBAC tests for the protected super-admin role."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.rbac import SUPER_ADMIN_ROLE_NAME
from app.core.security import create_access_token, hash_password
from app.database.models.permission import Permission
from app.database.models.role import Role
from app.database.models.user import User
from app.database.seeders.rbac_seeder import seed_permissions, seed_roles
from app.exceptions.common import ValidationException
from app.services.auth.authorization_service import AuthorizationService
from app.services.auth.role_service import RoleService


def test_seeded_super_admin_has_all_permissions_and_admin_does_not(db_session):
    """The bootstrap roles separate system and document administration."""
    permission_map = seed_permissions(db_session)
    role_map = seed_roles(db_session, permission_map)

    super_permissions = {
        permission.name
        for permission in role_map[SUPER_ADMIN_ROLE_NAME].permissions
    }

    assert super_permissions == set(permission_map)

def test_super_admin_role_cannot_be_created_updated_or_deleted(
    db_session,
    permission_1,
):
    """Protected-role operations fail before permissions can be changed."""
    service = RoleService(db_session)
    protected_role = db_session.scalar(
        select(Role).where(Role.name == SUPER_ADMIN_ROLE_NAME)
    )
    if protected_role is None:
        protected_role = Role(
            name=SUPER_ADMIN_ROLE_NAME,
            description="Protected",
        )
        protected_role.permissions = [permission_1]
        db_session.add(protected_role)
        db_session.commit()

    with pytest.raises(ValidationException):
        service.create_role(SUPER_ADMIN_ROLE_NAME, "Duplicate", [])
    with pytest.raises(ValidationException):
        service.update_role(
            protected_role.id,
            SUPER_ADMIN_ROLE_NAME,
            "Changed",
            [],
        )
    with pytest.raises(ValidationException):
        service.delete_role(protected_role.id)


def test_normal_admin_cannot_manage_users(client, db_session, active_user):
    """A document administrator does not receive system-user permissions."""
    permission = Permission(
        name=f"document.read.{uuid4().hex}",
        description="Document-read test permission",
    )
    role = Role(name=f"admin-{uuid4().hex}", description="Normal admin")
    role.permissions = [permission]
    user = User(
        email=f"normal-admin-{uuid4().hex}@example.com",
        password_hash=hash_password("Admin@123456"),
        is_active=True,
    )
    user.roles = [role]
    db_session.add_all([permission, role, user])
    db_session.commit()

    token, _ = create_access_token(user.id)
    response = client.get(
        f"/users/{active_user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_admin_role_name_does_not_bypass_permission_checks(db_session):
    """Authorization remains permission-based rather than role-name based."""
    permission = Permission(
        name="document.create",
        description="Document-create test permission",
    )
    role = Role(name="admin", description="Normal admin")
    role.permissions = [permission]
    user = User(
        email=f"admin-{uuid4().hex}@example.com",
        password_hash=hash_password("Admin@123456"),
        is_active=True,
    )
    user.roles = [role]
    db_session.add_all([permission, role, user])
    db_session.commit()

    authorization = AuthorizationService(db_session)
    assert authorization.has_permission(user, "document.create")
    assert not authorization.has_permission(user, "user.create")
