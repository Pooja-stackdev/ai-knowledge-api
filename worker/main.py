import logging
import time

from app.api.dependencies.document import create_document_service
from app.api.dependencies.document_worker import create_worker_dependencies
from app.api.dependencies.query import (
    get_embedding_service,
    get_vector_service,
)
from app.application.document_worker_service import DocumentWorkerService
from app.core.config import settings
from app.core.logging import setup_logging
from app.database.connection import SessionLocal
from app.database.repositories.document import DocumentRepository
from app.database.repositories.document_chunk import DocumentChunkRepository
from app.database.repositories.document_role import DocumentRoleRepository
from app.database.repositories.notification_outbox_repository import (
    NotificationOutboxRepository,
)
from app.database.repositories.role_repository import RoleRepository
from app.rag.chunker import DocumentChunker
from app.rag.loaders.factory import DocumentLoaderFactory
from app.services.knowledge.document_service import DocumentService
from app.services.knowledge.ingestion_service import DocumentIngestionService
from app.services.notifications.email_provider import SmtpEmailProvider
from app.services.notifications.notification_service import NotificationService
from app.storage.local_storage import LocalFileStorage

POLL_INTERVAL = 5
BATCH_SIZE = 10


def run_worker() -> None:
    """Run document ingestion and email-outbox dispatch in one worker process."""
    setup_logging()

    logger = logging.getLogger(__name__)

    logger.info("Document worker started")

    while True:
        db = SessionLocal()

        try:
            dependencies = create_worker_dependencies(db)

            worker_service = dependencies.worker_service

            recovered_documents = worker_service.recover_stuck_documents(
                timeout_minutes=settings.processing_timeout_minutes,
            )

            recovered_notifications = (
                worker_service.recover_stuck_notification_dispatches()
            )

            worker_service.process_pending_documents(
                limit=BATCH_SIZE,
            )

            delivered_notifications = (
                worker_service.dispatch_notifications()
            )

            logger.info(
                "Worker iteration completed",
                extra={
                    "recovered_documents": recovered_documents,
                    "recovered_notifications": recovered_notifications,
                    "delivered_notifications": delivered_notifications,
                },
            )


        except Exception:
            logger.exception("Document worker failed")

        finally:
            db.close()

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    print("Starting document worker...")
    run_worker()
