from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies.authentication import (
    AuthServiceDependency,
    CurrentUser,
    oauth2_scheme,
)
from app.exceptions.auth import AuthenticationException
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)



@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    service: AuthServiceDependency,
):
    return service.authenticate(
        email=form_data.username,
        password=form_data.password,
    )

@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh_token(
    request: RefreshTokenRequest,
    service: AuthServiceDependency,
):
    try:
        return service.refresh_access_token(
            request.refresh_token,
        )
    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
    ) as exc:
        raise AuthenticationException(
            "Invalid refresh token"
        ) from exc


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    access_token: Annotated[
        str,
        Depends(oauth2_scheme),
    ],
    service: AuthServiceDependency,
):
    try:
        service.logout(access_token)
    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
    ) as exc:
        raise AuthenticationException(
            "Invalid token"
        ) from exc
    

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: CurrentUser,
):
    return current_user

