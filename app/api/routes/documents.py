from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies.authorization import (
    get_current_user_role_ids,
    require_permission,
)
from app.api.dependencies.document import get_document_service
from app.api.dependencies.document_role import get_document_role_service
from app.database.models.user import User
from app.schemas.document import DocumentResponse
from app.schemas.document_role import DocumentRoleRequest, DocumentRoleResponse
from app.services.knowledge.document_role_service import DocumentRoleService
from app.services.knowledge.document_service import DocumentService

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
    current_user: Annotated[User, Depends(require_permission("document.create"))],
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
    current_user: Annotated[
        User,
        Depends(require_permission("document.read")),
    ],
    role_ids: Annotated[
        list[int],
        Depends(get_current_user_role_ids),
    ],
    service: DocumentServiceDep,
) -> DocumentResponse:
    return service.get_accessible_document(
        document_id=document_id,
        role_ids=role_ids,
    )


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
    service.delete_document(document_id)


@router.get(
    "",
    response_model=list[DocumentResponse],
)
def list_documents(
    current_user: Annotated[
        User,
        Depends(require_permission("document.read")),
    ],
    role_ids: Annotated[
        list[int],
        Depends(get_current_user_role_ids),
    ],
    service: DocumentServiceDep,
):
    return service.get_documents(
        role_ids=role_ids,
    )


@router.put(
    "/{document_id}/roles",
    response_model=DocumentRoleResponse,
    dependencies=[
        Depends(require_permission("document.access.manage")),
    ],
)
def assign_document_roles(
    document_id: int,
    request: DocumentRoleRequest,
    service: Annotated[
        DocumentRoleService,
        Depends(get_document_role_service),
    ],
):
    role_ids = service.replace_roles(
        document_id=document_id,
        role_ids=request.role_ids,
    )

    return DocumentRoleResponse(
        document_id=document_id,
        role_ids=role_ids,
    )