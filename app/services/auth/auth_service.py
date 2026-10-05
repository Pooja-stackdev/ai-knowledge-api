import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.database.repositories.auth_repository import AuthRepository
from app.database.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.database.repositories.user_repository import UserRepository
from app.exceptions.auth import AuthenticationException
from app.exceptions.common import (
    BadRequestException,
    ResourceNotFoundException,
)
from app.schemas.auth import TokenResponse
from app.services.notifications.email_provider import EmailProvider
from app.services.notifications.email_templates import (
    password_reset_message,
)


class AuthService:

    def __init__(self, db: Session,user_repository:UserRepository,auth_repository:AuthRepository,password_reset_token_repository:PasswordResetTokenRepository,email_provider: EmailProvider,):
        self.db = db
        self.user_repository = user_repository
        self.auth_repository = auth_repository
        self.password_reset_token_repository = password_reset_token_repository
        self.email_provider = email_provider

    def authenticate(
        self,
        email: str,
        password: str,
    ) -> TokenResponse:
        user = self.user_repository.get_by_email(email)

        if user is None:
            raise AuthenticationException(
                "auth.credentials_invalid"
            )

        if not verify_password(password, user.password_hash):
            raise AuthenticationException(
                "auth.credentials_invalid"
            )

        if not user.is_active:
            raise AuthenticationException(
                "auth.credentials_invalid"
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
            raise AuthenticationException("auth.invalid_refresh_token")

        user_id = int(payload["sub"])

        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise AuthenticationException("user.not_found")

        if not user.is_active:
            raise AuthenticationException("auth.credentials_invalid")

        access_token, _ = create_access_token(user.id)
        new_refresh_token, _ = create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )

    def get_current_user(self, user_id: int):
        user = self.user_repository.get_by_id(user_id)

        print("CURRENT USER:", user)
        print("CURRENT USER ID:", user.id if user else None)
        print("CURRENT USER ACTIVE:", user.is_active if user else None)

        if user is None:
            raise ResourceNotFoundException(
                resource="User",
                resource_id=user_id
            )

        if not user.is_active:
            raise AuthenticationException("auth.credentials_invalid")

        return user

   
    def logout(self, access_token: str) -> None:
        payload = decode_token(access_token)

        jti = payload.get("jti")

        if not jti:
            raise ValueError("Token does not contain jti")

        expires_at = datetime.fromtimestamp(
            payload["exp"],
            tz=timezone.utc,
        )

        if not self.auth_repository.is_token_revoked(jti):
            self.auth_repository.revoke_token(
                jti=jti,
                expires_at=expires_at,
            )

        print("logout")

        self.db.commit()


    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        confirm_new_password: str,
    ) -> None:


        user = self.user_repository.get_by_id(user_id)

        if not user:
            raise ResourceNotFoundException(
                resource="User",
                resource_id=user_id
            )

        if new_password != confirm_new_password:
            raise BadRequestException(
                "auth.new_password_confirmation_not_match"
            )

        if not verify_password(
            current_password,
            user.password_hash,
        ):
            raise BadRequestException(
                "auth.current_password_incorrect",
            )

        if current_password == new_password:
            raise BadRequestException(
                "auth.new_password_must_be_diff",
            )

        password_hash = hash_password(new_password)

        self.user_repository.update_password(
            user=user,
            password_hash=password_hash,
        )

    def forgot_password(self, email: str) -> None:
        user = self.user_repository.get_by_email(email)

        if not user:
            return

        raw_token = secrets.token_urlsafe(32)

        token_hash = hashlib.sha256(
            raw_token.encode()
        ).hexdigest()

        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=30
        )

        """ Prevent multiple active reset tokens """
        self.password_reset_token_repository.invalidate_active_tokens(
            user.id
        )

        self.password_reset_token_repository.create(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )


        message = password_reset_message(
            recipient_email=user.email,
            reset_token=raw_token,
        )

        self.email_provider.send(message)
        
        self.db.commit()

    def reset_password(
        self,
        *,
        token: str,
        new_password: str,
        confirm_new_password: str,
    ) -> None:

        if new_password != confirm_new_password:
            raise BadRequestException(
                "auth.new_password_confirmation_not_match"
            )

        
        token_hash = hashlib.sha256(
            token.encode()
        ).hexdigest()

        reset_token = (
            self.password_reset_token_repository
            .get_by_token_hash(token_hash)
        )
       
        if not reset_token:
            raise BadRequestException(
                "auth.invalid_expire_reset_token"
            )

        now = datetime.now(timezone.utc)

        if reset_token.used_at is not None:
            raise BadRequestException(
                "auth.invalid_expire_reset_token"
            )

        if reset_token.expires_at <= now:
            raise BadRequestException(
                "auth.invalid_expire_reset_token"
            )

        user = self.user_repository.get_by_id(
            reset_token.user_id
        )

        if not user:
            raise ResourceNotFoundException(
                resource="User",
                resource_id=reset_token.user_id,
            )

        if verify_password(
            new_password,
            user.password_hash,
        ):
            raise BadRequestException(
                "auth.new_password_must_be_diff"
            )
        

        user.password_hash = hash_password(new_password)

        self.password_reset_token_repository.mark_as_used(
            reset_token
        )

        self.db.commit()
