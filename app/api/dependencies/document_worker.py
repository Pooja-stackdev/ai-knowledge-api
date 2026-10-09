from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.api.dependencies.document import create_document_service
from app.api.dependencies.query import (
    get_embedding_service,
    get_vector_service,
)
from app.application.document_worker_service import DocumentWorkerService
from app.core.config import settings
from app.database.repositories.document_chunk import DocumentChunkRepository
from app.database.repositories.notification_outbox_repository import (
    NotificationOutboxRepository,
)
from app.rag.chunker import DocumentChunker
from app.rag.loaders.factory import DocumentLoaderFactory
from app.services.knowledge.document_service import DocumentService
from app.services.knowledge.ingestion_service import DocumentIngestionService
from app.services.notifications.email_provider import SmtpEmailProvider
from app.services.notifications.notification_service import NotificationService
from app.storage.local_storage import LocalFileStorage


@dataclass
class WorkerDependencies:
    document_service: DocumentService
    worker_service: DocumentWorkerService

def create_worker_dependencies(db: Session) -> WorkerDependencies:
    storage = LocalFileStorage(
        base_path=settings.document_storage_path,
    )

    chunk_repository = DocumentChunkRepository(db)

    notification_service = NotificationService(
        session=db,
        repository=NotificationOutboxRepository(db),
        email_provider=(
            SmtpEmailProvider()
            if settings.smtp_enabled
            else None
        ),
    )

    embedding_service = get_embedding_service()
    vector_service = get_vector_service()

    document_service = create_document_service(
        db=db,
        storage=storage,
        chunk_repository=chunk_repository,
        vector_service=vector_service,
    )

    ingestion_service = DocumentIngestionService(
        loader_factory=DocumentLoaderFactory(),
    )

    worker_service = DocumentWorkerService(
        document_service=document_service,
        ingestion_service=ingestion_service,
        chunker=DocumentChunker(),
        embedding_service=embedding_service,
        vector_service=vector_service,
        notification_service=notification_service,
    )

    return WorkerDependencies(
        document_service=document_service,
        worker_service=worker_service,
    )