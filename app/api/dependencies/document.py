from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.authorization import get_current_user_role_ids
from app.api.dependencies.query import get_vector_service
# from app.api.dependencies.role import get_user_role_repository
from app.core.config import settings
from app.database.connection import get_db_session
from app.database.models.document import Document
from app.database.repositories.document import DocumentRepository
from app.database.repositories.document_chunk import DocumentChunkRepository
from app.database.repositories.document_role import DocumentRoleRepository
from app.database.repositories.role_repository import RoleRepository
from app.services.knowledge.document_service import DocumentService
from app.services.knowledge.vector_service import VectorService
from app.storage.local_storage import LocalFileStorage


def get_document_storage() -> LocalFileStorage:
    return LocalFileStorage(
        base_path=settings.document_storage_path,
    )


def get_document_chunk_repository(
    db: Annotated[Session, Depends(get_db_session)],
) -> DocumentChunkRepository:
    return DocumentChunkRepository(db)


def get_document_repository(
    db: Annotated[Session, Depends(get_db_session)],
) -> DocumentRepository:
    return DocumentRepository(db)

def get_document_role_repository(
    db: Annotated[Session, Depends(get_db_session)],
) -> DocumentRoleRepository:
    return DocumentRoleRepository(db)

def create_document_service(
    db: Session,
    storage: LocalFileStorage,
    chunk_repository: DocumentChunkRepository,
    vector_service: VectorService,
) -> DocumentService:

    repository = DocumentRepository(db)
    document_role_repository = DocumentRoleRepository(db)
    role_repository = RoleRepository(db)

    return DocumentService(
        db=db,
        repository=repository,
        document_role_repository=document_role_repository,
        role_repository=role_repository,
        storage=storage,
        chunk_repository=chunk_repository,
        vector_service=vector_service,
    )

# def get_document_service(
#     db: Annotated[Session, Depends(get_db_session)],
#     repository: Annotated[
#         DocumentRepository,
#         Depends(get_document_repository),
#     ],
#     storage: Annotated[
#         LocalFileStorage,
#         Depends(get_document_storage),
#     ],
#     chunk_repository: Annotated[
#         DocumentChunkRepository,
#         Depends(get_document_chunk_repository),
#     ],
#     vector_service: Annotated[
#         VectorService,
#         Depends(get_vector_service),
#     ],
#     document_role_repository: Annotated[
#         DocumentRoleRepository,
#         Depends(get_document_role_repository),
#     ],
#     role_repository: Annotated[
#         RoleRepository,
#         Depends(get_user_role_repository),
#     ],
# ) -> DocumentService:
#     return DocumentService(
#         db=db,
#         repository=repository,
#         document_role_repository=document_role_repository,
#         storage=storage,
#         chunk_repository=chunk_repository,
#         vector_service=vector_service,
#         role_repository=role_repository,
#     )

def get_document_service(
    db: Annotated[Session, Depends(get_db_session)],
    storage: Annotated[LocalFileStorage, Depends(get_document_storage)],
    chunk_repository: Annotated[
        DocumentChunkRepository,
        Depends(get_document_chunk_repository),
    ],
    vector_service: Annotated[
        VectorService,
        Depends(get_vector_service),
    ],
) -> DocumentService:

    return create_document_service(
        db=db,
        storage=storage,
        chunk_repository=chunk_repository,
        vector_service=vector_service,
    )


def get_accessible_document(
    document_id: int,
    role_ids: Annotated[
        list[int],
        Depends(get_current_user_role_ids),
    ],
    service: Annotated[
        DocumentService,
        Depends(get_document_service),
    ],
) -> Document:
    return service.get_accessible_document(
        document_id=document_id,
        role_ids=role_ids,
    )