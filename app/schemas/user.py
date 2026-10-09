from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    role_ids: list[int] | None
    permissions: list[str] | None

    model_config = ConfigDict(from_attributes=True)

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role_ids: list[int] = []

class UpdateUserRequest(BaseModel):
    email: EmailStr | None = None
    role_ids: list[int] | None = None



