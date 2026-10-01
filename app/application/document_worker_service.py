import logging

from app.database.models.document import Document
from app.exceptions import AppException

logger = logging.getLogger(__name__)

class DocumentWorkerService:

    def __init__(
        self,
        document_service,
        ingestion_service,
        chunker,
        embedding_service,
        vector_service,
    ) -> None:
        self.document_service = document_service
        self.ingestion_service = ingestion_service
        self.chunker = chunker
        self.embedding_service = embedding_service
        self.vector_service = vector_service

    def process_pending_documents(
        self,
        limit: int = 10,
    ) -> int:
        documents = self.document_service.claim_documents(
            limit=limit,
        )

        logger.info(f"Processing document :{documents}")

        processed_count = 0

        for document in documents:
            if self.process_document(document):
                processed_count += 1

        return processed_count

    def process_document(
        self,
        document: Document,
    ) -> bool:
        try:

            logger.info(
                "Starting document processing",
                extra={"document_id": document.id},
            )
            
            existing_chunks = self.document_service.get_chunks(
                document.id,
            )

            logger.info(
                "Existing chunks fetched",
                extra={"existing_chunks count": len(existing_chunks)},
            )

            existing_chunk_ids = [
                chunk.id
                for chunk in existing_chunks
            ]

            logger.info(
                "Existing chunk IDs: %s",
                extra={"existing_chunk_ids": existing_chunk_ids},
            )

            self.vector_service.delete_embeddings(
                existing_chunk_ids,
            )

            self.document_service.clear_document_chunks(
                document.id,
            )

            loaded_document = self.ingestion_service.extract_text(
                filename=document.filename,
                storage_path=document.storage_path,
            )

            chunks = self.chunker.chunk(
                loaded_document,
            )

            if not chunks:
                raise AppException(
                    "Document contains no usable chunks",
                )

            database_chunks = self.document_service.save_chunks(
                document_id=document.id,
                chunks=chunks,
            )

            embeddings = self.embedding_service.embed_texts(
                [chunk.content for chunk in database_chunks],
            )

            logger.info(
                f"embeddings length:{len(embeddings)}, "
                f"database_chunks len:{len(database_chunks)}"
            )
            
            if len(embeddings) != len(database_chunks):
                raise AppException(
                    "Embedding count does not match chunk count",
                )

            self.vector_service.add_embeddings(
                chunk_ids=[
                    chunk.id
                    for chunk in database_chunks
                ],
                embeddings=embeddings,
            )

            self.document_service.mark_completed(
                document,
            )

            return True

        except (AppException, ValueError) as exc:
            self.document_service.mark_failed(
                document,
                str(exc),
            )

            return False

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