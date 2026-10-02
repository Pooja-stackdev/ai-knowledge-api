"""Application service for document-completion notification delivery."""

import logging

from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models.document import Document
from app.database.models.document_role import DocumentRole
from app.database.models.user import User
from app.database.models.user_role import UserRole
from app.domain.enums.document import DocumentStatus
from app.database.repositories.notification_outbox_repository import NotificationOutboxRepository
from app.services.notifications.email_provider import EmailProvider
from app.services.notifications.email_templates import document_completed_message

logger = logging.getLogger(__name__)


class NotificationService:
    """Queue and dispatch user notifications independently of document ingestion."""

    def __init__(
        self,
        session: Session,
        repository: NotificationOutboxRepository,
        email_provider: EmailProvider | None,
    ) -> None:
        self.session = session
        self.repository = repository
        self.email_provider = email_provider

    def enqueue_document_completed(self, document_id: int) -> int:
        """Create durable completion notifications for authorized active users."""
        document = self.session.get(Document, document_id)
        if document is None or document.status != DocumentStatus.COMPLETED:
            return 0
        recipients = self._recipient_emails(document_id)
        notifications = self.repository.create_many(document_id, recipients)
        self.session.commit()
        logger.info("Document notifications queued", extra={"document_id": document_id, "recipients": len(notifications)})
        return len(notifications)

    def dispatch_pending(self, limit: int | None = None) -> int:
        """Deliver a bounded batch of due records without affecting documents."""
        if self.email_provider is None:
            return 0
        notifications = self.repository.claim_pending(
            limit or settings.notification_batch_size,
            settings.notification_max_attempts,
        )
        self.session.commit()
        delivered = 0
        for notification in notifications:
            try:
                document = self.session.get(Document, notification.document_id)
                if document is None:
                    raise RuntimeError("Document no longer exists.")
                self.email_provider.send(document_completed_message(document, notification.recipient_email))
                self.repository.mark_sent(notification)
                self.session.commit()
                delivered += 1
            except Exception as exc:
                self.repository.mark_retry_or_failed(
                    notification,
                    type(exc).__name__,
                    settings.notification_max_attempts,
                    settings.notification_retry_base_seconds * (2 ** (notification.attempt_count - 1)),
                )
                self.session.commit()
                logger.warning("Notification delivery failed", extra={"notification_id": notification.id, "error_type": type(exc).__name__})
        return delivered

    def recover_stuck_dispatches(self) -> int:
        """Release notifications stranded in SENDING after a process failure."""
        recovered = self.repository.recover_stuck_sending(settings.notification_sending_timeout_minutes)
        self.session.commit()
        return recovered

    def _recipient_emails(self, document_id: int) -> list[str]:
        role_ids = list(self.session.scalars(select(DocumentRole.role_id).where(DocumentRole.document_id == document_id)))
        statement = select(distinct(User.email)).where(User.is_active.is_(True))
        if role_ids:
            statement = statement.join(UserRole, UserRole.user_id == User.id).where(UserRole.role_id.in_(role_ids))
        return sorted(email.lower() for email in self.session.scalars(statement).all())
