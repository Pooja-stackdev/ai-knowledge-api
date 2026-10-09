# app/schemas/document_role.py

from pydantic import BaseModel, Field


class DocumentRoleRequest(BaseModel):
    role_ids: list[int] = Field(default_factory=list)


class DocumentRoleResponse(BaseModel):
    document_id: int
    role_ids: list[int]