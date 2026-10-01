from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.document_chunk import DocumentChunk


class DocumentChunkRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def create(
        self,
        *,
        document_id: int,
        chunk_index: int,
        page_number: int,
        content: str,
    ) -> DocumentChunk:

        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=chunk_index,
            page_number=page_number,
            content=content,
        )

        self.db.add(chunk)

        return chunk

    def create_many(
        self,
        chunks: list[DocumentChunk],
    ) -> Sequence[DocumentChunk]:

        self.db.add_all(chunks)

        return chunks

    def get_by_document_id(
        self,
        document_id: int,
    ) -> Sequence[DocumentChunk]:

        statement = (
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id == document_id,
            )
            .order_by(
                DocumentChunk.chunk_index,
            )
        )

        return self.db.scalars(statement).all()

    def get_by_ids(
        self,
        chunk_ids: Sequence[int],
    ) -> Sequence[DocumentChunk]:

        if not chunk_ids:
            return []

        statement = select(DocumentChunk).where(
            DocumentChunk.id.in_(chunk_ids),
        )

        return self.db.scalars(statement).all()

    def delete_by_document_id(
        self,
        document_id: int,
    ) -> None:

        chunks = self.get_by_document_id(
            document_id,
        )

        for chunk in chunks:
            self.db.delete(chunk)


    def get_ids_by_document_ids(
        self,
        document_ids: list[int],
    ) -> list[int]:
        if not document_ids:
            return []

        return list(
            self.db.scalars(
                select(DocumentChunk.id).where(
                    DocumentChunk.document_id.in_(document_ids)
                )
            )
        )