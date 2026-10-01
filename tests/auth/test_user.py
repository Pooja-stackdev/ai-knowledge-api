from uuid import uuid4

from sqlalchemy import select

from app.database.models.role import Role
from app.database.models.user import User
from app.database.models.user_role import UserRole


def test_get_user(client, active_user, admin_access_token):
    response = client.get(
        f"/users/{active_user.id}",
        headers={
            "Authorization": f"Bearer {admin_access_token}"
        },
    )

    print(response.json())
    print(response.status_code)
    assert response.status_code == 200

    data = response.json()

    assert data["id"] == active_user.id
    assert data["email"] == active_user.email


def test_get_user_not_found(client, admin_access_token):
    response = client.get(
        "/users/999999",
        headers={
            "Authorization": f"Bearer {admin_access_token}"
        },
    )

    assert response.status_code == 404


def test_update_user_email(
    client,
    active_user,
    admin_access_token,
):
    new_email = f"updated-{uuid4().hex}@example.com"

    response = client.put(
        f"/users/{active_user.id}",
        headers={
            "Authorization": f"Bearer {admin_access_token}"
        },
        json={
            "email": new_email,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == active_user.id
    assert data["email"] == new_email


def test_update_user_duplicate_email(
    client,
    active_user,
    inactive_user,
    admin_access_token,
):
    response = client.put(
        f"/users/{active_user.id}",
        headers={
            "Authorization": f"Bearer {admin_access_token}"
        },
        json={
            "email": inactive_user.email,
        },
    )

    assert response.status_code == 409


def test_update_user_roles(
    client,
    active_user,
    permission_1,
    db_session,
    admin_access_token,
):
    role = Role(
        name=f"editor-{uuid4().hex[:8]}",
        description="Test editor role",
    )

    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)

    response = client.put(
        f"/users/{active_user.id}",
        headers={
            "Authorization": f"Bearer {admin_access_token}"
        },
        json={
            "role_ids": [role.id],
        },
    )

    assert response.status_code == 200

    user_role = db_session.scalar(
        select(UserRole).where(
            UserRole.user_id == active_user.id,
            UserRole.role_id == role.id,
        )
    )

    assert user_role is not None


def test_update_user_cannot_assign_admin_role(
    client,
    active_user,
    admin_role,
    admin_access_token,
):
    response = client.put(
        f"/users/{active_user.id}",
        headers={
            "Authorization": f"Bearer {admin_access_token}"
        },
        json={
            "role_ids": [admin_role.id],
        },
    )

    assert response.status_code == 400
    assert response.json()["message"] == (
        "The admin role cannot be assigned manually"
    )


def test_update_user_role_not_found(
    client,
    active_user,
    admin_access_token,
):
    response = client.put(
        f"/users/{active_user.id}",
        headers={
            "Authorization": f"Bearer {admin_access_token}"
        },
        json={
            "role_ids": [999999],
        },
    )

    assert response.status_code == 404


def test_update_user_not_found(
    client,
    admin_access_token,
):
    response = client.put(
        "/users/999999",
        headers={
            "Authorization": f"Bearer {admin_access_token}"
        },
        json={
            "email": "new@example.com",
        },
    )

    assert response.status_code == 404


def test_delete_user(
    client,
    db_session,
    active_user,
    admin_access_token,
):
    user_id = active_user.id

    response = client.delete(
        f"/users/{user_id}",
        headers={
            "Authorization": f"Bearer {admin_access_token}"
        },
    )

    assert response.status_code == 204

    deleted_user = db_session.scalar(
        select(User).where(User.id == user_id)
    )

    assert deleted_user is None


def test_delete_user_not_found(
    client,
    admin_access_token,
):
    response = client.delete(
        "/users/999999",
        headers={
            "Authorization": f"Bearer {admin_access_token}"
        },
    )

    assert response.status_code == 404