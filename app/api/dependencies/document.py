"""FastAPI dependencies for document-related endpoints."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.query import get_vector_service
from app.core.config import settings
from app.database.connection import get_db_session
from app.database.repositories.document import DocumentRepository
from app.database.repositories.document_chunk import DocumentChunkRepository
from app.services.document_service import DocumentService
from app.services.knowledge.vector_service import VectorService
from app.storage.local_storage import LocalFileStorage


def get_document_storage() -> LocalFileStorage:
    """Create the local document storage implementation."""
    return LocalFileStorage(
        base_path=settings.document_storage_path,
    )


def get_document_chunk_repository(
    db: Annotated[Session, Depends(get_db_session)],
) -> DocumentChunkRepository:
    """Create a document chunk repository using the request database session."""
    return DocumentChunkRepository(db)


def get_document_repository(
    db: Annotated[Session, Depends(get_db_session)],
) -> DocumentRepository:
    """Create a document repository using the request database session."""
    return DocumentRepository(db)


def get_document_service(
    db: Annotated[Session, Depends(get_db_session)],
    repository: Annotated[
        DocumentRepository,
        Depends(get_document_repository),
    ],
    storage: Annotated[
        LocalFileStorage,
        Depends(get_document_storage),
    ],
    chunk_repository: Annotated[
        DocumentChunkRepository,
        Depends(get_document_chunk_repository),
    ],
    vector_service: Annotated[
        VectorService,
        Depends(get_vector_service),
    ],
) -> DocumentService:
    """Create the document service with its required infrastructure dependencies."""
    return DocumentService(
        db=db,
        repository=repository,
        storage=storage,
        chunk_repository=chunk_repository,
        vector_service=vector_service,
    )