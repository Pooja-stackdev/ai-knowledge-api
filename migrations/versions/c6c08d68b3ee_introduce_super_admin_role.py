"""Introduce the protected super-admin role.

Revision ID: c6c08d68b3ee
Revises: 770946c85e79
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c6c08d68b3ee"
down_revision: str | Sequence[str] | None = "770946c85e79"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SUPER_ADMIN_ROLE_NAME = "super_admin"
NORMAL_ADMIN_PERMISSIONS = {
    "document.create",
    "document.read",
    "document.delete",
    "query.execute",
    "document.access.manage",
}


def _tables() -> tuple[sa.Table, sa.Table, sa.Table, sa.Table]:
    """Describe the RBAC tables needed for this data migration."""
    metadata = sa.MetaData()
    roles = sa.Table(
        "roles",
        metadata,
        sa.Column("id", sa.Integer),
        sa.Column("name", sa.String),
        sa.Column("description", sa.String),
    )
    permissions = sa.Table("permissions", metadata, sa.Column("id", sa.Integer), sa.Column("name", sa.String))
    role_permissions = sa.Table(
        "role_permissions",
        metadata,
        sa.Column("role_id", sa.Integer),
        sa.Column("permission_id", sa.Integer),
    )
    user_roles = sa.Table(
        "user_roles",
        metadata,
        sa.Column("user_id", sa.Integer),
        sa.Column("role_id", sa.Integer),
    )
    return roles, permissions, role_permissions, user_roles


def upgrade() -> None:
    """Preserve existing admin access by migrating it to super-admin."""
    bind = op.get_bind()
    roles, permissions, role_permissions, user_roles = _tables()

    super_admin_id = bind.scalar(
        sa.select(roles.c.id).where(roles.c.name == SUPER_ADMIN_ROLE_NAME)
    )
    if super_admin_id is None:
        super_admin_id = bind.execute(
            sa.insert(roles).values(
                name=SUPER_ADMIN_ROLE_NAME,
                description="Full system access",
            ).returning(roles.c.id)
        ).scalar_one()

    permission_rows = bind.execute(sa.select(permissions.c.id, permissions.c.name)).all()
    permission_ids = {name: permission_id for permission_id, name in permission_rows}
    bind.execute(sa.delete(role_permissions).where(role_permissions.c.role_id == super_admin_id))
    bind.execute(
        sa.insert(role_permissions),
        [{"role_id": super_admin_id, "permission_id": permission_id} for permission_id in permission_ids.values()],
    )

    admin_id = bind.scalar(sa.select(roles.c.id).where(roles.c.name == "admin"))
    if admin_id is None:
        return

    previous_admin_users = bind.execute(
        sa.select(user_roles.c.user_id).where(user_roles.c.role_id == admin_id)
    ).scalars().all()
    for user_id in previous_admin_users:
        exists = bind.scalar(
            sa.select(user_roles.c.user_id).where(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == super_admin_id,
            )
        )
        if exists is None:
            bind.execute(sa.insert(user_roles).values(user_id=user_id, role_id=super_admin_id))

    bind.execute(sa.delete(role_permissions).where(role_permissions.c.role_id == admin_id))
    bind.execute(
        sa.insert(role_permissions),
        [
            {"role_id": admin_id, "permission_id": permission_ids[name]}
            for name in NORMAL_ADMIN_PERMISSIONS
            if name in permission_ids
        ],
    )


def downgrade() -> None:
    """Restore legacy admin permissions and remove the super-admin role."""
    bind = op.get_bind()
    roles, permissions, role_permissions, user_roles = _tables()
    super_admin_id = bind.scalar(sa.select(roles.c.id).where(roles.c.name == SUPER_ADMIN_ROLE_NAME))
    admin_id = bind.scalar(sa.select(roles.c.id).where(roles.c.name == "admin"))
    if super_admin_id is None or admin_id is None:
        return

    permission_ids = bind.execute(sa.select(permissions.c.id)).scalars().all()
    bind.execute(sa.delete(role_permissions).where(role_permissions.c.role_id == admin_id))
    bind.execute(
        sa.insert(role_permissions),
        [{"role_id": admin_id, "permission_id": permission_id} for permission_id in permission_ids],
    )
    super_admin_users = bind.execute(
        sa.select(user_roles.c.user_id).where(user_roles.c.role_id == super_admin_id)
    ).scalars().all()
    for user_id in super_admin_users:
        exists = bind.scalar(
            sa.select(user_roles.c.user_id).where(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == admin_id,
            )
        )
        if exists is None:
            bind.execute(sa.insert(user_roles).values(user_id=user_id, role_id=admin_id))
    bind.execute(sa.delete(roles).where(roles.c.id == super_admin_id))
