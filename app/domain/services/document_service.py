import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models.document import Document
from app.database.repositories.document_repository import (
    DocumentRepository,
)
from app.domain.enums.document import DocumentStatus
from app.domain.validators.document_lifecycle import validate_transition
from app.domain.validators.document_validator import DocumentValidator
from app.exceptions.common import ResourceNotFoundException
from app.storage.local_storage import LocalFileStorage

logger = logging.getLogger(__name__)


class DocumentService:

    def __init__(
        self,
        db: Session,
        repository: DocumentRepository,
        storage: LocalFileStorage,
    ):
        self.db = db
        self.repository = repository
        self.storage = storage

    def get_document(
        self,
        document_id: int,
    ) -> Document | None:

        
        return self.repository.get_by_id(document_id)

    async def upload_document(
        self,
        file,
        filename: str,
        content_type: str,
        description: str | None = None,
    ):
        DocumentValidator.validate(
            filename=filename,
            content_type=content_type,
            file_size=0,
        )

        stored_path = self.storage.create_path(filename)

        try:
            file_size = await self.storage.save_stream(
                file=file,
                destination=stored_path,
                max_size=settings.max_upload_size,
            )

            DocumentValidator.validate(
                filename=filename,
                content_type=content_type,
                file_size=file_size,
            )

            document = self.repository.create(
                filename=filename,
                content_type=content_type,
                description=description,
                storage_path=str(stored_path),
            )

            self.db.commit()
            self.db.refresh(document)

            return document

        except Exception:
            self.db.rollback()
            stored_path.unlink(missing_ok=True)
            raise

    def claim_documents(
        self,
        limit: int = 10,
    ):
        try:
            documents = self.repository.claim_pending_documents(
                limit=limit,
            )

            self.db.commit()

            return documents

        except Exception:
            self.db.rollback()
            raise

    def mark_processing(
        self,
        document: Document,
    ):
        return self._change_status(
            document=document,
            new_status=DocumentStatus.PROCESSING,
        )

    def mark_completed(
        self,
        document: Document,
    ):
        return self._change_status(
            document=document,
            new_status=DocumentStatus.COMPLETED,
        )

    def mark_failed(
        self,
        document: Document,
        error: str,
    ):
        validate_transition(
            current=document.status,
            new=DocumentStatus.FAILED,
        )

        try:
            document.status = DocumentStatus.FAILED
            document.last_error = error
            document.processing_started_at = None

            self.db.commit()
            self.db.refresh(document)

            return document

        except Exception:
            self.db.rollback()
            raise

    def retry_document(
        self,
        document_id: int,
    ):
        document = self.repository.get_by_id(document_id)

        if document is None:
            raise ResourceNotFoundException(
                resource="Document",
                resource_id=document_id,
            )

        validate_transition(
            current=document.status,
            new=DocumentStatus.PENDING,
        )

        if document.attempt_count >= settings.max_processing_attempts:
            raise ValueError(
                "Maximum processing attempts exceeded"
            )

        try:
            document.status = DocumentStatus.PENDING
            document.processing_started_at = None
            document.last_error = None

            self.db.commit()
            self.db.refresh(document)

            return document

        except Exception:
            self.db.rollback()
            raise

    def recover_stuck_documents(
        self,
        timeout_minutes: int,
    ) -> int:
        documents = self.repository.get_stuck_processing_documents(
            timeout_minutes=timeout_minutes,
        )
        print("hiiiiiiiiii")
        print(list(documents))
        recovered = 0

        try:
            for document in documents:

                print(
                    f"QUERY RESULT: id={document.id}, "
                    f"status={document.status}, "
                    f"attempt_count={document.attempt_count}, "
                    f"processing_started_at={document.processing_started_at}"
                    f"max_processing_attempts={settings.max_processing_attempts}"
                )
                if (
                    document.attempt_count
                    >= settings.max_processing_attempts
                ):
                    print(document.status)
                    document.status = DocumentStatus.FAILED
                    document.last_error = (
                        "Maximum processing attempts exceeded"
                    )
                    document.processing_started_at = None

                else:
                    document.status = DocumentStatus.PENDING
                    document.processing_started_at = None
                    document.last_error = (
                        "Worker processing timeout"
                    )

                recovered += 1

            self.db.commit()
            print(recovered)

            return recovered

        except Exception:
            self.db.rollback()

            logger.exception("Document recover worker iteration failed")
            raise

    def _change_status(
        self,
        document: Document,
        new_status: DocumentStatus,
    ):
        validate_transition(
            current=document.status,
            new=new_status,
        )

        try:
            self.repository.update_status(
                document,
                new_status,
            )

            self.db.commit()
            self.db.refresh(document)

            return document

        except Exception:
            self.db.rollback()
            raise

