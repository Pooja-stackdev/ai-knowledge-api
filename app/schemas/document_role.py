# app/schemas/document_role.py

from pydantic import BaseModel, Field


class DocumentRoleRequest(BaseModel):
    role_ids: list[int] = Field(min_length=1)


class DocumentRoleResponse(BaseModel):
    document_id: int
    role_ids: list[int]