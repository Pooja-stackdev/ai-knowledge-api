from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    filename: str
    content_type: str
    description: str | None = None


class DocumentResponse(BaseModel):
    id: int
    filename: str
    status: str
    content_type: str
    description: str | None
    storage_path: str
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)