import logging
import time

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
from app.rag.chunker import DocumentChunker
from app.rag.loaders.factory import DocumentLoaderFactory
from app.services.knowledge.document_service import DocumentService
from app.services.knowledge.ingestion_service import DocumentIngestionService
from app.storage.local_storage import LocalFileStorage

POLL_INTERVAL = 5
BATCH_SIZE = 10


def run_worker():
    setup_logging()

    logger = logging.getLogger(__name__)

    logger.info("Document worker started")

    while True:
        db = SessionLocal()

        try:
            repository = DocumentRepository(db)

            storage = LocalFileStorage(
                base_path=settings.document_storage_path,
            )

            chunk_repository = DocumentChunkRepository(db)

            # Infrastructure services
            embedding_service = get_embedding_service()
            vector_service = get_vector_service()

            # Document service
            document_service = DocumentService(
                db=db,
                repository=repository,
                storage=storage,
                chunk_repository=chunk_repository,
                vector_service=vector_service,
            )

            loader_factory = DocumentLoaderFactory()

            ingestion_service = DocumentIngestionService(
                loader_factory=loader_factory,
            )

            chunker = DocumentChunker()

            # Worker application service
            worker_service = DocumentWorkerService(
                document_service=document_service,
                ingestion_service=ingestion_service,
                chunker=chunker,
                embedding_service=embedding_service,
                vector_service=vector_service,
            )

            worker_service.process_pending_documents(
                limit=BATCH_SIZE,
            )

            logger.info("Successfully processed pending documents")

        except Exception:
            logger.exception("Document worker failed")

        finally:
            db.close()

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    print("Starting document worker...")
    run_worker()