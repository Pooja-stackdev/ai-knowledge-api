from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies.authentication import (
    AuthServiceDependency,
    CurrentUser,
    oauth2_scheme,
)
from app.core.i18n import get_message
from app.exceptions.auth import AuthenticationException
from app.schemas.auth import (
    AuthResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
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
            "auth.invalid_refresh_token"
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
            "auth.invalid_token"
        ) from exc
    

@router.get(
    "/me",
    response_model=AuthResponse,
)
def get_me(
    current_user: CurrentUser,
    service: AuthServiceDependency
):
    return service.get_user_profile(user=current_user)

@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
)
def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser,
    service: AuthServiceDependency,
):
    service.change_password(
        user_id=current_user.id,
        current_password=request.current_password,
        new_password=request.new_password,
        confirm_new_password=request.confirm_new_password,
    )


@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    service: AuthServiceDependency,
):
    service.forgot_password(request.email)

    return {
        "message": get_message(
            "auth.password_reset_email_sent"
        )
    }

@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    service: AuthServiceDependency,
):
    service.reset_password(
        token=request.token,
        new_password=request.new_password,
        confirm_new_password=request.confirm_new_password,
    )

    return {
        "message": get_message(
            "auth.password_reset_success"
        )
    }