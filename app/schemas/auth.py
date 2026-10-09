from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    username: EmailStr
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
    confirm_new_password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(
        min_length=8,
        max_length=128,
    )
    confirm_new_password: str

class RoleSummary(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    roles: list[RoleSummary]
    permissions: list[str]

    model_config = ConfigDict(from_attributes=True)