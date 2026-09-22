from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import get_db_session
from app.database.repositories.document_repository import (
    DocumentRepository,
)
from app.domain.services.document_service import DocumentService
from app.schemas.document import DocumentResponse
from app.storage.local_storage import LocalFileStorage

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

DbSession = Annotated[
    Session,
    Depends(get_db_session),
]



def get_document_service(
    db: DbSession,
) -> DocumentService:

    repository = DocumentRepository(db)

    storage = LocalFileStorage(
        base_path=settings.storage_path,
    )

    return DocumentService(
        db=db,
        repository=repository,
        storage=storage,
    )


DocumentServiceDep = Annotated[
    DocumentService,
    Depends(get_document_service),
]

@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=201,
)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    description: Annotated[str | None, Form()] = None,
    service: DocumentServiceDep = None,
):
    return await service.upload_document(
        file=file,
        filename=file.filename or "",
        content_type=file.content_type,
        description=description,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: int,
    service: DocumentServiceDep = None,
):
    document = service.get_document(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document