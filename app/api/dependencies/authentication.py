from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.connection import get_db_session
from app.database.models.user import User
from app.database.repositories.auth_repository import AuthRepository
from app.database.repositories.user_repository import UserRepository
from app.exceptions.auth import AuthenticationException
from app.exceptions.common import ResourceNotFoundException
from app.services.auth.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False,
)


def get_auth_service(
    db: Annotated[Session, Depends(get_db_session)],
) -> AuthService:
    return AuthService(
        db=db,
        user_repository=UserRepository(db=db),
        auth_repository=AuthRepository(db=db),
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

        service = get_auth_service(db)

        if service.auth_repository.is_token_revoked(jti):
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
        return service.get_current_user(user_id)

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
