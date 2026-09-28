from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies.authentication import (
    AuthServiceDependency,
    CurrentUser,
    oauth2_scheme,
)
from app.schemas.auth import (
    LogoutRequest,
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
    try:
        return service.authenticate(
            email=form_data.username,
            password=form_data.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    request: LogoutRequest,
    access_token: Annotated[
        str,
        Depends(oauth2_scheme),
    ],
    service: AuthServiceDependency,
):
    try:
        service.logout(
            access_token=access_token,
            refresh_token=request.refresh_token,
        )
    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: CurrentUser,
):
    return current_user


# @router.post(
#     "/register",
#     response_model=UserResponse,
#     status_code=status.HTTP_201_CREATED,
# )
# def register(
#     request: LoginRequest,
#     service: AuthServiceDependency,
# ):
#     try:
#         return service.create_user(
#             email=request.email,
#             password=request.password,
#         )
#     except ValueError as exc:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail=str(exc),
#         ) from exc