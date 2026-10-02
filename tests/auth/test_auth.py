

def test_login_success(client, active_user):
    response = client.post(
        "/auth/login",
        data={
            "username": active_user.email,
            "password": "Test@123456",
        },
    )

    print("STATUS:", response.status_code)
    print("RESPONSE:", response.json())
    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_invalid_password(client, active_user):
    response = client.post(
        "/auth/login",
        data={
            "username": active_user.email,
            "password": "WrongPassword@123",
        },
    )

    print("STATUS:", response.status_code)
    print("RESPONSE:", response.json())
    assert response.status_code == 401
    assert response.json()["message"] == "Could not validate credentials."


def test_login_with_unknown_user(client):
    response = client.post(
        "/auth/login",
        data={
            "username": "does-not-exist@example.com",
            "password": "Test@123456",
        },
    )

    assert response.status_code == 401
    assert response.json()["message"] == "Could not validate credentials."


def test_login_with_inactive_user(client, inactive_user):
    response = client.post(
        "/auth/login",
        data={
            "username": inactive_user.email,
            "password": "Test@123456",
        },
    )

    assert response.status_code == 401
    assert response.json()["message"] == "Could not validate credentials."


def test_get_current_user_success(
    client,
    active_user,
    access_token,
):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == active_user.id
    assert data["email"] == active_user.email


def test_get_current_user_without_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401

    assert response.json()["message"] == "Unauthorized."


def test_get_current_user_with_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401

    assert response.json()["message"] == "Unauthorized."


def test_get_current_user_with_refresh_token(
    client,
    active_user,
):
    from app.core.security import create_refresh_token

    refresh_token, _ = create_refresh_token(active_user.id)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {refresh_token}",
        },
    )

    assert response.status_code == 401
    assert response.json()["message"] == "Invalid access token."


def test_get_current_user_with_invalid_user_id(client):
    from app.core.security import create_access_token

    access_token, _ = create_access_token(999999)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 401
    assert response.json()["message"] == "Could not validate credentials."


def test_refresh_token_success(
    client,
    active_user,
    refresh_token,
):
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_with_invalid_token(client):
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": "invalid-refresh-token",
        },
    )

    assert response.status_code == 401
    assert response.json()["message"] == "Invalid refresh token"


def test_logout_success(
    client,
    active_user,
    access_token,
    refresh_token,
):
    response = client.post(
        "/auth/logout",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 204


def test_logout_without_access_token(
    client,
    refresh_token,
):
    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 401


def test_logout_with_invalid_access_token(
    client,
    refresh_token,
):
    response = client.post(
        "/auth/logout",
        headers={
            "Authorization": "Bearer invalid-token",
        },
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 401
