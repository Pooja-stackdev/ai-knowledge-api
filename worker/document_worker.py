import logging
import time

from app.application.document_worker_service import DocumentWorkerService
from app.core.config import settings

logger = logging.getLogger(__name__)

class DocumentWorker:
    def __init__(
        self,
        worker_service: DocumentWorkerService,
        poll_interval: int = 5,
    ):
        self.worker_service = worker_service
        self.poll_interval = poll_interval

    def run(self) -> None:
        logger.info("Document worker started")

        while True:
            try:
                processed_count = (
                    self.worker_service.process_pending_documents()
                )

                if processed_count == 0:
                    time.sleep(self.poll_interval)

            except Exception:
                logger.exception(
                    "Document worker iteration failed"
                )

                time.sleep(self.poll_interval)

    # def run_once(self):
    #     self.service.recover_stuck_documents(
    #         timeout_minutes=settings.processing_timeout_minutes,
    #     )

    #     documents = self.service.claim_documents(
    #         limit=10,
    #     )

    #     for document in documents:
    #         self.process(document)