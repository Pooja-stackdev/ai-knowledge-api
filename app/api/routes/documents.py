from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies.authorization import require_permission
from app.api.dependencies.document import get_document_service
from app.database.models.user import User
from app.exceptions.common import ResourceNotFoundException
from app.schemas.document import DocumentResponse
from app.services.document_service import DocumentService

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
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
    service: DocumentServiceDep,
    current_user: Annotated[User, Depends(require_permission("document.upload"))],
    description: Annotated[str | None, Form()] = None,
) -> DocumentResponse:
    
    """Upload a document for processing."""
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
    current_user: Annotated[User, Depends(require_permission("document.read"))],
    service: DocumentServiceDep = None,
):
    """Retrieve a document by its ID."""
    document = service.get_document(document_id)

    if document is None:
        raise ResourceNotFoundException(
            resource="Document",
            resource_id=document_id,
        )

    return document

@router.delete(
    "/{document_id}",
    status_code=204,
)
def delete_document(
    document_id: int,
    service: DocumentServiceDep,
    current_user: Annotated[
        User,
        Depends(require_permission("document.delete")),
    ],
) -> None:
    """Delete a document and its associated data."""

    service.delete_document(document_id)