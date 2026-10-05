import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models.document import Document
from app.database.models.document_chunk import DocumentChunk
from app.database.repositories.document import (
    DocumentRepository,
)
from app.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from app.domain.enums.document import DocumentStatus
from app.domain.validators.document_lifecycle import validate_transition
from app.domain.validators.document_validator import DocumentValidator
from app.exceptions.auth import AuthorizationException
from app.exceptions.base import (
    AppException,
)
from app.exceptions.common import (
    ResourceNotFoundException,
)
from app.services.knowledge.vector_service import VectorService
from app.storage.local_storage import LocalFileStorage

logger = logging.getLogger(__name__)


class DocumentService:

    def __init__(
        self,
        db: Session,
        repository: DocumentRepository,
        storage: LocalFileStorage,
        chunk_repository: DocumentChunkRepository,
        vector_service: VectorService,
    ):
        self.db = db
        self.repository = repository
        self.storage = storage
        self.chunk_repository = chunk_repository
        self.vector_service = vector_service

    def get_document(
        self,
        document_id: int,
    ) -> Document:
        document = self.repository.get_by_id(document_id)

        if document is None:
            raise ResourceNotFoundException(
                resource="Document",
                resource_id=document_id,
            )

        return document


    def get_accessible_document(
        self,
        document_id: int,
        role_ids: list[int],
    ) -> Document:
        document = self.repository.get_by_id(document_id)

        if document is None:
            raise ResourceNotFoundException(
                resource="Document",
                resource_id=document_id,
            )

        accessible_document = self.repository.get_accessible_by_id(
            document_id=document_id,
            role_ids=role_ids,
        )

        if accessible_document is None:
            raise AuthorizationException(
                message="document.forbidden",
            )

        return accessible_document
    

    async def upload_document(
        self,
        file,
        filename: str,
        content_type: str,
        description: str | None = None,
    ) -> Document:
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

        except AppException:
            self.db.rollback()

            stored_path.unlink(missing_ok=True)

            raise

    def claim_documents(
        self,
        limit: int = 10,
    ) -> list[Document]:
        try:
            documents = self.repository.claim_pending_documents(
                limit=limit,
            )

            self.db.commit()

            return documents

        except AppException:
            self.db.rollback()
            raise

    def mark_processing(
        self,
        document: Document,
    ) -> Document:
        return self._change_status(
            document=document,
            new_status=DocumentStatus.PROCESSING,
        )

    def mark_completed(
        self,
        document: Document,
    ) -> Document:
        return self._change_status(
            document=document,
            new_status=DocumentStatus.COMPLETED,
        )

    def mark_failed(
        self,
        document: Document,
        error: str,
    ) -> Document:
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

        except AppException:
            self.db.rollback()
            raise

    def retry_document(
        self,
        document_id: int,
    ) -> Document:
        logger.info(f"retry document id:{document_id}")
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

        logger.info(f"retry document id:{document_id}, attempt_count:{document.attempt_count}")
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

        except AppException:
            self.db.rollback()
            raise

    def recover_stuck_documents(
        self,
        timeout_minutes: int,
    ) -> int:
        documents = self.repository.get_stuck_processing_documents(
            timeout_minutes=timeout_minutes,
        )

        logger.info(f"get recover documents:{documents}")
       
        recovered = 0

        try:
            for document in documents:

                if (
                    document.attempt_count
                    >= settings.max_processing_attempts
                ):
                    
                    document.status = DocumentStatus.FAILED
                    document.last_error = (
                        "Maximum processing attempts exceeded"
                    )

                else:
                    document.status = DocumentStatus.PENDING
                    document.last_error = (
                        "Worker processing timeout"
                    )

                document.processing_started_at = None
                recovered += 1

            self.db.commit()

            return recovered

        except AppException:
            self.db.rollback()

            logger.exception("Document recover worker iteration failed")
            raise


    def save_chunks(
        self,
        *,
        document_id: int,
        chunks: list[DocumentChunk],
    ) -> list[DocumentChunk]:
        try:
            database_chunks = [
                DocumentChunk(
                    document_id=document_id,
                    chunk_index=chunk.chunk_index,
                    page_number=chunk.page_number,
                    content=chunk.content,
                )
                for chunk in chunks
            ]

            self.chunk_repository.create_many(
                database_chunks,
            )

            self.db.commit()

            for chunk in database_chunks:
                self.db.refresh(chunk)

            return database_chunks

        except AppException:
            self.db.rollback()
            raise


    def clear_document_chunks(
        self,
        document_id: int,
    ) -> None:
        try:
            self.chunk_repository.delete_by_document_id(
                document_id,
            )

            self.db.commit()

        except AppException:
            self.db.rollback()
            raise

    def get_chunks(
        self,
        document_id: int,
    ):
        return self.chunk_repository.get_by_document_id(
            document_id,
        )

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
    
            except AppException:
                self.db.rollback()
                raise


    def delete_document(
        self,
        document_id: int,
    ) -> None:

        document = self.get_document(document_id)

        chunks = self.chunk_repository.get_by_document_id(
            document_id,
        )

        chunk_ids = [chunk.id for chunk in chunks]

        try:
            self.vector_service.delete_embeddings(chunk_ids)

            self.chunk_repository.delete_by_document_id(
                document_id,
            )

            self.repository.delete(document)

            self.db.commit()

            self.storage.delete(
                Path(document.storage_path),
            )

        except AppException:
            self.db.rollback()
            raise

    def get_documents(
        self,
        role_ids: list[int],
    ) -> list[Document]:
        return self.repository.get_accessible_documents(
            role_ids=role_ids,
        )
