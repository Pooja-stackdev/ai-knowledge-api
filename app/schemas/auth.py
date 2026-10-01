from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.enums.languages import Language


class LoginRequest(BaseModel):
    username: EmailStr
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    language: Language

    model_config = ConfigDict(from_attributes=True)

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role_ids: list[int] = []
    language: Language = Language.EN

class UpdateUserRequest(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)
    role_ids: list[int] | None = None
    language: Language | None = None