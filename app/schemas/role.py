# app/schemas/role.py

from pydantic import BaseModel, Field


class RoleCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    permission_ids: list[int] = []

class RoleUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    permission_ids: list[int] = Field(default_factory=list)



class RoleResponse(BaseModel):
    id: int
    name: str
    description: str | None
    permission_ids: list[int]



class RoleListResponse(BaseModel):
    roles: list[RoleResponse]