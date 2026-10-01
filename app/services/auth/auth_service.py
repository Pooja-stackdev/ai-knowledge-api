from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.database.repositories.auth_repository import AuthRepository
from app.database.repositories.user_repository import UserRepository
from app.exceptions.auth import AuthenticationException
from app.exceptions.common import ResourceNotFoundException
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

        if user is None:
            raise AuthenticationException(
                "Could not validate credentials."
            )

        if not verify_password(password, user.password_hash):
            raise AuthenticationException(
                "Could not validate credentials."
            )

        if not user.is_active:
            raise AuthenticationException(
                "Could not validate credentials."
            )

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
            raise AuthenticationException("Invalid refresh token")

        user_id = int(payload["sub"])

        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise AuthenticationException("User not found")

        if not user.is_active:
            raise AuthenticationException("User account is inactive")

        access_token, _ = create_access_token(user.id)
        new_refresh_token, _ = create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )

    def get_current_user(self, user_id: int):
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ResourceNotFoundException(
                resource="User",
                resource_id=user_id
            )

        if not user.is_active:
            raise AuthenticationException("User account is inactive")

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