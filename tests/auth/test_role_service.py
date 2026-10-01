from uuid import uuid4

import pytest

from app.exceptions.common import ResourceNotFoundException
from app.services.auth.role_service import RoleService


def unique_role_name(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def test_create_role_with_permissions(
    db_session,
    permission_1,
    permission_2,
):
    service = RoleService(db_session)

    role_name = unique_role_name("support")

    role = service.create_role(
        name=role_name,
        description="Support team",
        permission_ids=[
            permission_1.id,
            permission_2.id,
        ],
    )

    assert role["name"] == role_name
    assert role["description"] == "Support team"
    assert set(role["permission_ids"]) == {
        permission_1.id,
        permission_2.id,
    }


def test_create_role_without_permissions(
    db_session,
):
    service = RoleService(db_session)

    role_name = unique_role_name("viewer")

    role = service.create_role(
        name=role_name,
        description="Read-only user",
        permission_ids=[],
    )

    assert role["name"] == role_name
    assert role["permission_ids"] == []


def test_create_role_with_invalid_permission(
    db_session,
    permission_1,
):
    service = RoleService(db_session)

    role_name = unique_role_name("support")

    with pytest.raises(ResourceNotFoundException):
        service.create_role(
            name=role_name,
            description="Support team",
            permission_ids=[
                permission_1.id,
                999999,
            ],
        )

def test_update_role_permissions(
    db_session,
    permission_1,
    permission_2,
):
    service = RoleService(db_session)

    role_name = unique_role_name("support")

    role = service.create_role(
        name=role_name,
        description="Support team",
        permission_ids=[
            permission_1.id,
        ],
    )

    updated = service.update_role(
        role_id=role["id"],
        name=role_name,
        description="Updated support team",
        permission_ids=[
            permission_2.id,
            permission_1.id,
        ],
    )

    assert updated["name"] == role_name
    assert updated["description"] == "Updated support team"
    assert set(updated["permission_ids"]) == {
        permission_1.id,
        permission_2.id,
    }


def test_update_role_removes_all_permissions(
    db_session,
    permission_1,
):
    service = RoleService(db_session)

    role_name = unique_role_name("support")

    role = service.create_role(
        name=role_name,
        description="Support team",
        permission_ids=[permission_1.id],
    )

    updated = service.update_role(
        role_id=role["id"],
        name=role_name,
        description="Support team",
        permission_ids=[],
    )

    assert updated["permission_ids"] == []


def test_create_role_deduplicates_permissions(
    db_session,
    permission_1,
):
    service = RoleService(db_session)

    role_name = unique_role_name("support")

    role = service.create_role(
        name=role_name,
        description="Support team",
        permission_ids=[
            permission_1.id,
            permission_1.id,
        ],
    )

    assert role["permission_ids"] == [permission_1.id]
