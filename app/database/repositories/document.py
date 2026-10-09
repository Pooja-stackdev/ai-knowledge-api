from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database.models.document import Document
from app.database.models.document_role import DocumentRole
from app.domain.enums.document import DocumentStatus


class DocumentRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        filename: str,
        content_type: str,
        storage_path: str,
        description: str | None = None,
    ) -> Document:

        document = Document(
            filename=filename,
            content_type=content_type,
            description=description,
            storage_path=storage_path,
            status=DocumentStatus.PENDING,
        )

        self.db.add(document)

        self.db.flush()

        return document

    def get_by_id(self, document_id: int) -> Document | None:
        statement = select(Document).where(
            Document.id == document_id
        )

        return self.db.scalar(statement)

    def update_status(
        self,
        document,
        status: DocumentStatus,
    ):
        document.status = status

        self.db.add(document)

        return document


    def get_pending_documents(
        self,
        limit: int = 10,
    ) -> list[Document]:
        statement = (
            select(Document)
            .where(
                Document.status == DocumentStatus.PENDING
            )
            .order_by(Document.created_at)
            .limit(limit)
        )

        return list(
            self.db.scalars(statement).all()
        )

    def claim_pending_documents(
        self,
        limit: int = 10,
    ) -> list[Document]:

        statement = (
            select(Document)
            .where(
                Document.status == DocumentStatus.PENDING
            )
            .order_by(Document.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )

        documents = list(
            self.db.scalars(statement).all()
        )

        for document in documents:
            document.status = DocumentStatus.PROCESSING
            document.processing_started_at = datetime.now(timezone.utc)
            document.attempt_count += 1
            document.last_error = None

        self.db.flush()

        return documents

    def get_stuck_processing_documents(
        self,
        timeout_minutes: int,
    ) -> list[Document]:

        cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=timeout_minutes
        )

        statement = (
            select(Document)
            .where(
                Document.status == DocumentStatus.PROCESSING,
                Document.processing_started_at.is_not(None),
                Document.processing_started_at < cutoff,
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    def delete(
        self,
        document: Document,
    ) -> None:
        self.db.delete(document)


    def get_accessible_document_ids(
        self,
        role_ids: list[int],
    ) -> list[int]:

        query = (
            select(Document.id)
            .outerjoin(
                DocumentRole,
                DocumentRole.document_id == Document.id,
            )
        )

        if role_ids:
            query = query.where(
                DocumentRole.role_id.in_(role_ids)
            )
            # query = query.where(
            #     or_(
            #         DocumentRole.role_id.is_(None),
            #         DocumentRole.role_id.in_(role_ids),
            #     )
            # )
        else:
            # query = query.where(
            #     DocumentRole.role_id.is_(None)
            # )
            return []

        return list(
            self.db.scalars(query).unique()
        )


    def get_accessible_by_id(
        self,
        document_id: int,
        role_ids: list[int],
    ) -> Document | None:

        statement = (
            select(Document)
            .outerjoin(
                DocumentRole,
                DocumentRole.document_id == Document.id,
            )
            .where(Document.id == document_id)
        )

        if role_ids:
            statement = statement.where(
                DocumentRole.role_id.in_(role_ids),
            )
        else:
           return None

        return self.db.scalar(statement)

    def get_accessible_documents(
        self,
        role_ids: list[int],
    ) -> list[Document]:

        statement = (
            select(Document)
            .outerjoin(
                DocumentRole,
                DocumentRole.document_id == Document.id,
            )
        )

        if role_ids:
            statement = statement.where(
                or_(
                    DocumentRole.role_id.is_(None),
                    DocumentRole.role_id.in_(role_ids),
                )
            )
        else:
            statement = statement.where(
                DocumentRole.role_id.is_(None)
            )

        statement = statement.distinct().order_by(Document.created_at.desc())

        return list(self.db.scalars(statement))