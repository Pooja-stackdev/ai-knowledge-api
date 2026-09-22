from app.domain.services.document_service import DocumentService
from app.exceptions import AppException


class DocumentWorkerService:

    def __init__(
        self,
        document_service: DocumentService,
    ):
        self.document_service = document_service

    def process_pending_documents(
        self,
        limit: int = 10,
    ) -> int:
        documents = self.document_service.claim_documents(
            limit=limit,
        )

        processed_count = 0

        for document in documents:
            self.process_document(document)
            processed_count += 1

        return processed_count

    def process_document(
        self,
        document,
    ) -> None:
        try:
            # Actual PDF processing will be added later:
            #
            # 1. Load document
            # 2. Extract text
            # 3. Split into chunks
            # 4. Generate embeddings
            # 5. Store vectors

            self.document_service.mark_completed(
                document,
            )

        except AppException as exc:
            self.document_service.mark_failed(
                document,
                str(exc),
            )

    def retry_document(
        self,
        document_id: int,
    ):
        return self.document_service.retry_document(
            document_id,
        )

    def recover_stuck_documents(
        self,
        timeout_minutes: int,
    ) -> int:
        return self.document_service.recover_stuck_documents(
            timeout_minutes=timeout_minutes,
        )

