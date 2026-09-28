from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.database.models.user import User
from app.database.repositories.auth_repository import AuthRepository
from app.database.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse


class AuthService:

    def __init__(self, db: Session,user_repository:UserRepository,auth_repository:AuthRepository):
        self.db = db
        self.user_repository = user_repository
        self.auth_repository = auth_repository

    def authenticate(
        self,
        email: str,
        password: str,
    ) -> TokenResponse:
        user = self.user_repository.get_by_email(email)
        print(f"User--->{user}")

        print("Stored hash:", user.password_hash)
        print(
            "Password valid:",
            verify_password(password, user.password_hash),
        )
        if user is None:
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("User account is inactive")

        print("User is active")

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise ValueError("Invalid email or password")

        print(f"User--->{user}")

        user.last_login_at = datetime.now(timezone.utc)

        self.db.commit()

        access_token, _ = create_access_token(user.id)
        refresh_token, _ = create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def refresh_access_token(
        self,
        refresh_token: str,
    ) -> TokenResponse:
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")

        user_id = int(payload["sub"])

        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found")

        if not user.is_active:
            raise ValueError("User account is inactive")

        access_token, _ = create_access_token(user.id)
        new_refresh_token, _ = create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )

    def get_current_user(self, user_id: int):
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found")

        if not user.is_active:
            raise ValueError("User account is inactive")

        return user

    def create_user(
        self,
        email: str,
        password: str,
    ):
        existing_user = self.user_repository.get_by_email(email)

        if existing_user is not None:
            raise ValueError("User already exists")

        user = self.user_repository.create(
            email=email,
            password_hash=hash_password(password),
        )

        self.db.commit()

        return user

    def logout(
        self,
        access_token: str,
        refresh_token: str,
    ) -> None:
        for token in (access_token, refresh_token):
            payload = decode_token(token)

            jti = payload.get("jti")

            if not jti:
                continue

            expires_at = datetime.fromtimestamp(
                payload["exp"],
                tz=timezone.utc,
            )

            if not self.auth_repository.is_token_revoked(jti):
                self.auth_repository.revoke_token(
                    jti=jti,
                    expires_at=expires_at,
                )

        self.db.commit()