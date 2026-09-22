import time

from app.application.document_worker_service import (
    DocumentWorkerService,
)
from app.core.config import settings
from app.database.connection import SessionLocal
from app.database.repositories.document_repository import (
    DocumentRepository,
)
from app.domain.services.document_service import DocumentService
from app.storage.local_storage import LocalFileStorage

POLL_INTERVAL = 5
BATCH_SIZE = 10


def run_worker():
    print("Document worker started")

    while True:
        db = SessionLocal()

        try:
            repository = DocumentRepository(db)

            storage = LocalFileStorage(
                base_path=settings.storage_path,
            )

            document_service = DocumentService(
                db=db,
                repository=repository,
                storage=storage,
            )

            worker_service = DocumentWorkerService(
                document_service=document_service,
            )

            worker_service.process_pending_documents(
                limit=BATCH_SIZE,
            )

        finally:
            db.close()

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_worker()

