from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.connection import get_db_session
from app.database.models.user import User
from app.database.repositories.auth_repository import AuthRepository
from app.database.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.database.repositories.user_repository import UserRepository
from app.exceptions.auth import AuthenticationException
from app.exceptions.common import ResourceNotFoundException
from app.services.auth.auth_service import AuthService
from app.services.notifications.email_provider import EmailProvider, SmtpEmailProvider

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False,
)

def get_email_provider() -> EmailProvider:
    return SmtpEmailProvider()

def get_auth_service(
    db: Annotated[Session, Depends(get_db_session)],
    email_provider: Annotated[
        EmailProvider,
        Depends(get_email_provider),
    ],
) -> AuthService:
    return AuthService(
        db=db,
        user_repository=UserRepository(db=db),
        auth_repository=AuthRepository(db=db),
        password_reset_token_repository=PasswordResetTokenRepository(
            db=db,
        ),
        email_provider=email_provider,
    )


AuthServiceDependency = Annotated[
    AuthService,
    Depends(get_auth_service),
]



def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db_session)],
) -> User:

    try:
        if token is None:
            raise AuthenticationException("auth.unauthorized")

        payload = decode_token(token)

        if payload.get("type") != "access":
            raise AuthenticationException(
                "auth.invalid_access_token",
            )

        jti = payload.get("jti")

        if not jti:
            raise AuthenticationException(
                "auth.invalid_access_token",
            )

        auth_repository = AuthRepository(db)

        if auth_repository.is_token_revoked(jti):
            raise AuthenticationException(
                "auth.token_revoked",
            )

        user_id = payload.get("sub")

        if user_id is None:
            raise AuthenticationException(
                "auth.invalid_token",
            )

        user_id = int(user_id)

    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
    ) as exc:
        raise AuthenticationException(
            "auth.unauthorized",
        ) from exc

    try:
        # user = UserRepository(db).get_by_id(user_id)
        user = UserRepository(db).get_current_user_by_id_with_permissions(user_id)
        if user is None:
            raise ResourceNotFoundException(
                resource="User",
                resource_id=user_id,
            )
        if not user.is_active:
            raise AuthenticationException("auth.credentials_invalid")
        return user

    except ResourceNotFoundException as exc:
        raise AuthenticationException(
            "auth.credentials_invalid",
        ) from exc

    except AuthenticationException as exc:
        raise AuthenticationException(
            "auth.unauthorized",
        ) from exc

CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]
