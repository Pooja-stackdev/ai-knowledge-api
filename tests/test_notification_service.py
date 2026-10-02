"""Tests for durable document-completion notifications."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from app.database.models.document import Document
from app.database.models.document_role import DocumentRole
from app.database.models.notification_outbox import NotificationOutbox
from app.database.models.role import Role
from app.database.models.user import User
from app.database.models.user_role import UserRole
from app.database.repositories.notification_outbox_repository import NotificationOutboxRepository
from app.domain.enums.document import DocumentStatus
from app.services.notifications.email_provider import EmailProvider
from app.services.notifications.notification_service import NotificationService
from app.application.document_worker_service import DocumentWorkerService


class FakeEmailProvider(EmailProvider):
    """Captures email messages without any network delivery."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.messages = []

    def send(self, message) -> None:
        if self.should_fail:
            raise RuntimeError("SMTP unavailable")
        self.messages.append(message)


def _document(db_session, status: DocumentStatus = DocumentStatus.COMPLETED) -> Document:
    db_session.query(NotificationOutbox).delete()
    db_session.commit()
    document = Document(
        filename="handbook.pdf",
        storage_path="storage/documents/handbook.pdf",
        content_type="application/pdf",
        status=status,
    )
    db_session.add(document)
    db_session.commit()
    return document


def _service(db_session, provider: EmailProvider | None) -> NotificationService:
    return NotificationService(
        session=db_session,
        repository=NotificationOutboxRepository(db_session),
        email_provider=provider,
    )


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def test_role_based_recipients_are_active_and_deduplicated(db_session):
    document = _document(db_session)
    first_role = Role(name="notifications-first")
    second_role = Role(name="notifications-second")
    active_email = _email("active")
    active_user = User(email=active_email, password_hash="x", is_active=True)
    inactive_user = User(email=_email("inactive"), password_hash="x", is_active=False)
    db_session.add_all([first_role, second_role, active_user, inactive_user])
    db_session.flush()
    db_session.add_all(
        [
            DocumentRole(document_id=document.id, role_id=first_role.id),
            DocumentRole(document_id=document.id, role_id=second_role.id),
            UserRole(user_id=active_user.id, role_id=first_role.id),
            UserRole(user_id=active_user.id, role_id=second_role.id),
            UserRole(user_id=inactive_user.id, role_id=first_role.id),
        ]
    )
    db_session.commit()

    service = _service(db_session, FakeEmailProvider())
    assert service.enqueue_document_completed(document.id) == 1
    assert [item.recipient_email for item in db_session.query(NotificationOutbox).all()] == [active_email]
    assert service.enqueue_document_completed(document.id) == 0


def test_no_role_document_notifies_all_active_users(db_session):
    document = _document(db_session)
    db_session.add_all(
        [
            User(email=_email("first"), password_hash="x", is_active=True),
            User(email=_email("second"), password_hash="x", is_active=True),
            User(email=_email("inactive"), password_hash="x", is_active=False),
        ]
    )
    db_session.commit()

    active_user_count = db_session.scalar(
        select(func.count()).select_from(User).where(User.is_active.is_(True))
    )
    assert _service(db_session, FakeEmailProvider()).enqueue_document_completed(document.id) == active_user_count


def test_pending_or_failed_documents_do_not_create_notifications(db_session):
    document = _document(db_session, status=DocumentStatus.FAILED)
    assert _service(db_session, FakeEmailProvider()).enqueue_document_completed(document.id) == 0


def test_dispatch_marks_successfully_sent_notifications(db_session):
    document = _document(db_session)
    db_session.add(User(email=_email("recipient"), password_hash="x", is_active=True))
    db_session.commit()
    provider = FakeEmailProvider()
    service = _service(db_session, provider)
    service.enqueue_document_completed(document.id)

    notifications = db_session.query(NotificationOutbox).filter_by(document_id=document.id).all()
    assert service.dispatch_pending() == len(notifications)
    assert all(notification.status == "SENT" for notification in notifications)
    assert all(notification.sent_at is not None for notification in notifications)
    assert len(provider.messages) == len(notifications)


def test_dispatch_failure_is_retried_and_eventually_fails(db_session):
    document = _document(db_session)
    db_session.add(User(email=_email("recipient"), password_hash="x", is_active=True))
    db_session.commit()
    service = _service(db_session, FakeEmailProvider(should_fail=True))
    service.enqueue_document_completed(document.id)

    assert service.dispatch_pending() == 0
    notifications = db_session.query(NotificationOutbox).filter_by(document_id=document.id).all()
    assert all(notification.status == "RETRY" for notification in notifications)
    notification = notifications[0]
    assert notification.next_attempt_at is not None
    notification.status = "PENDING"
    notification.next_attempt_at = datetime.now(timezone.utc)
    notification.attempt_count = 4
    db_session.commit()

    service.dispatch_pending()
    assert notification.status == "FAILED"


def test_disabled_dispatcher_leaves_outbox_pending(db_session):
    document = _document(db_session)
    db_session.add(User(email=_email("recipient"), password_hash="x", is_active=True))
    db_session.commit()
    service = _service(db_session, None)
    service.enqueue_document_completed(document.id)

    assert service.dispatch_pending() == 0
    notifications = db_session.query(NotificationOutbox).filter_by(document_id=document.id).all()
    assert all(notification.status == "PENDING" for notification in notifications)


def test_worker_queues_notifications_only_after_successful_processing():
    """A completed ingestion queues email work without sending it inline."""
    class DocumentService:
        def get_chunks(self, document_id):
            return []

        def clear_document_chunks(self, document_id):
            pass

        def save_chunks(self, **kwargs):
            return [type("Chunk", (), {"id": 11, "content": "Knowledge"})()]

        def mark_completed(self, document):
            self.completed = document.id

        def mark_failed(self, document, error):
            raise AssertionError(error)

    class IngestionService:
        def extract_text(self, **kwargs):
            return object()

    class Chunker:
        def chunk(self, document):
            return [object()]

    class EmbeddingService:
        def embed_texts(self, texts):
            return [[0.1]]

    class VectorService:
        def delete_embeddings(self, chunk_ids):
            pass

        def add_embeddings(self, **kwargs):
            pass

    class NotificationServiceFake:
        def enqueue_document_completed(self, document_id):
            self.queued_document_id = document_id

    document_service = DocumentService()
    notification_service = NotificationServiceFake()
    worker = DocumentWorkerService(
        document_service=document_service,
        ingestion_service=IngestionService(),
        chunker=Chunker(),
        embedding_service=EmbeddingService(),
        vector_service=VectorService(),
        notification_service=notification_service,
    )
    document = type("Document", (), {"id": 7, "filename": "handbook.txt", "storage_path": "handbook.txt"})()

    assert worker.process_document(document) is True
    assert document_service.completed == 7
    assert notification_service.queued_document_id == 7
