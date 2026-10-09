
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database.models.password_reset_token import PasswordResetToken


def test_login_success(client, active_user):
    response = client.post(
        "/auth/login",
        data={
            "username": active_user.email,
            "password": "Test@123456",
        },
    )

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




def test_forgot_password_existing_user(
    client,
    active_user,
    db_session,
):
    response = client.post(
        "/auth/forgot-password",
        json={
            "email": active_user.email,
        },
    )

    assert response.status_code == 200

    reset_token = (
        db_session.query(PasswordResetToken)
        .filter_by(user_id=active_user.id)
        .first()
    )

    assert reset_token is not None
    assert reset_token.used_at is None
    assert reset_token.expires_at is not None

    def test_forgot_password_invalid_email(
        client,
    ):
        response = client.post(
            "/auth/forgot-password",
            json={
                "email": "invalid-email",
            },
        )

        assert response.status_code == 422

    def test_reset_password_success(
        client,
        active_user,
        db_session,
        fake_email_provider,
    ):
        # Step 1: request password reset
        response = client.post(
            "/auth/forgot-password",
            json={
                "email": active_user.email,
            },
        )

        assert response.status_code == 200

        # Step 2: extract token from email
        message = fake_email_provider.messages[0]

        body = message.get_body(
            preferencelist=("plain",)
        ).get_content()

        import re

        match = re.search(
            r"[?&]token=([^\s]+)",
            body,
        )

        assert match is not None

        reset_token = match.group(1)

        # Step 3: reset password
        response = client.post(
            "/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "NewTest@123456",
                "confirm_new_password": "NewTest@123456",
            },
        )

        assert response.status_code == 200

        # Step 4: verify password was changed
        db_session.refresh(active_user)

        from app.core.security import verify_password

        assert verify_password(
            "NewTest@123456",
            active_user.password_hash,
        )

        # Step 5: verify token is consumed
        reset_token_record = db_session.scalar(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == active_user.id
            )
        )

        assert reset_token_record.used_at is not None

def test_reset_password_confirmation_mismatch(
    client,
    active_user,
    fake_email_provider,
):
    # Create reset token
    response = client.post(
        "/auth/forgot-password",
        json={
            "email": active_user.email,
        },
    )

    assert response.status_code == 200

    message = fake_email_provider.messages[0]

    body = message.get_body(
        preferencelist=("plain",)
    ).get_content()

    import re

    match = re.search(
        r"[?&]token=([^\s]+)",
        body,
    )

    assert match is not None

    reset_token = match.group(1)

    # Try reset with different confirmation password
    response = client.post(
        "/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": "NewTest@123456",
            "confirm_new_password": "Different@123456",
        },
    )

    assert response.status_code == 400

    def test_reset_password_invalid_token(
        client,
    ):
        response = client.post(
            "/auth/reset-password",
            json={
                "token": "invalid-reset-token",
                "new_password": "NewTest@123456",
                "confirm_new_password": "NewTest@123456",
            },
        )

        assert response.status_code == 400


    def test_reset_password_expired_token(
        client,
        active_user,
        db_session,
        fake_email_provider,
    ):
        # Create reset token
        response = client.post(
            "/auth/forgot-password",
            json={
                "email": active_user.email,
            },
        )

        assert response.status_code == 200

        message = fake_email_provider.messages[0]

        body = message.get_body(
            preferencelist=("plain",)
        ).get_content()

        import re

        match = re.search(
            r"[?&]token=([^\s]+)",
            body,
        )

        assert match is not None

        reset_token = match.group(1)

        # Expire the token
        token_record = db_session.scalar(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == active_user.id
            )
        )

        assert token_record is not None

        token_record.expires_at = datetime.now(timezone.utc) - timedelta(
            minutes=1
        )

        db_session.commit()

        # Try to reset password
        response = client.post(
            "/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "NewTest@123456",
                "confirm_new_password": "NewTest@123456",
            },
        )

        assert response.status_code == 400


def test_new_forgot_password_request_invalidates_previous_token(
    client,
    active_user,
    db_session,
    fake_email_provider,
):
    # First forgot-password request
    response = client.post(
        "/auth/forgot-password",
        json={
            "email": active_user.email,
        },
    )

    assert response.status_code == 200

    first_token_record = db_session.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == active_user.id
        )
    )

    assert first_token_record is not None
    assert first_token_record.used_at is None

    first_token_hash = first_token_record.token_hash

    # Second forgot-password request
    response = client.post(
        "/auth/forgot-password",
        json={
            "email": active_user.email,
        },
    )

    assert response.status_code == 200

    # Verify first token is invalidated
    db_session.refresh(first_token_record)

    assert first_token_record.token_hash == first_token_hash
    assert first_token_record.used_at is not None

    # Verify a new active token exists
    tokens = db_session.scalars(
        select(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == active_user.id
        )
        .order_by(PasswordResetToken.id)
    ).all()

    assert len(tokens) == 2

    second_token_record = tokens[-1]

    assert second_token_record.id != first_token_record.id
    assert second_token_record.used_at is None

def test_old_reset_token_fails_after_new_request(
    client,
    active_user,
    db_session,
    fake_email_provider,
):
    import re

    # First reset request
    response = client.post(
        "/auth/forgot-password",
        json={
            "email": active_user.email,
        },
    )

    assert response.status_code == 200

    first_message = fake_email_provider.messages[0]

    first_body = first_message.get_body(
        preferencelist=("plain",)
    ).get_content()

    first_match = re.search(
        r"[?&]token=([^\s]+)",
        first_body,
    )

    assert first_match is not None

    first_token = first_match.group(1)

    # Second reset request
    response = client.post(
        "/auth/forgot-password",
        json={
            "email": active_user.email,
        },
    )

    assert response.status_code == 200

    # Try using the old token
    response = client.post(
        "/auth/reset-password",
        json={
            "token": first_token,
            "new_password": "NewTest@123456",
            "confirm_new_password": "NewTest@123456",
        },
    )

    assert response.status_code == 400