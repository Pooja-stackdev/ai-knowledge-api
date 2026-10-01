# app/schemas/permission.py

from pydantic import BaseModel


class PermissionResponse(BaseModel):
    id: int
    name: str
    description: str | None